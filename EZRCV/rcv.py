from flask import (
    Blueprint, redirect, render_template, request, url_for, flash
)
from EZRCV import db
import sqlalchemy as sa
from EZRCV.models import Ballot, Entry, Voter
from collections import deque
import itertools

import pandas as pd
import plotly.express as px
import plotly.utils
import json

bp = Blueprint('rcv', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        if 'vote' in request.form:
            if request.form['voteCode'].isnumeric() and db.session.get(Ballot, request.form['voteCode']) is not None:
                return redirect(url_for('rcv.vote', ballot_id=request.form['voteCode']))
            else:
                flash("Vote short code does not exist!")
                return redirect((url_for('index')))
        elif 'results' in request.form:
            if (request.form['resultsCode'].isnumeric()
                    and db.session.get(Ballot, request.form['resultsCode']) is not None):
                return redirect(url_for('rcv.results', ballot_id=request.form['resultsCode']))
            else:
                flash("Results short code does not exist!")
                return redirect(url_for('index'))

    return render_template('index.html')


@bp.route('/create', methods=('GET', 'POST'))
def create_ballot():
    if request.method == "POST":
        name = request.form['name']
        display_records = 'display_records' in request.form
        allow_name = 'allow_name' in request.form
        entries = request.form.getlist('entries')

        ballot = Ballot(name=name, display_records=display_records, allow_name=allow_name)
        db.session.add(ballot)
        db.session.flush()
        for entry in entries:
            db.session.add(Entry(ballot_id=ballot.id, name=entry))
        db.session.commit()

        return redirect(url_for('rcv.create_ballot_success', ballot_id=ballot.id))

    return render_template('create-ballot.html')


@bp.route('/<int:ballot_id>/ballot_success')
def create_ballot_success(ballot_id):
    vote_link = request.url_root + f'{ballot_id}/vote'
    return render_template('ballot-success.html', link=vote_link, code=ballot_id)


@bp.route('/<int:ballot_id>/vote', methods=('GET', 'POST'))
def vote(ballot_id):
    if request.method == "POST":
        entry_ids = request.form.getlist('entry_ids')
        name = request.form.get('voter_name', 'Anon')
        if name == '':
            name = 'Anon'
        rankings = " ".join(entry_id for entry_id in entry_ids)
        db.session.add(Voter(ballot_id=ballot_id, name=name, vote=rankings))
        db.session.commit()

        return redirect(url_for('rcv.vote_success', ballot_id=ballot_id))

    entries = db.session.execute(sa.select(Entry).where(Entry.ballot_id == ballot_id))
    ballot_info = db.session.scalar(sa.select(Ballot).where(Ballot.id == ballot_id))

    return render_template('vote.html', entries=entries, ballot=ballot_info)


@bp.route('/<int:ballot_id>/vote_success')
def vote_success(ballot_id):
    results_link = request.url_root + f'{ballot_id}/results'
    return render_template('vote-success.html', link=results_link, code=ballot_id)


@bp.route('/<int:ballot_id>/results')
def results(ballot_id):
    """Returns a winner to the results template using the instant-runoff voting method. Optionally also displays
    various ballot statistics."""
    ballot_opts = db.session.scalar(sa.select(Ballot).where(Ballot.id == ballot_id))

    # rankings(votes) are stored as a list of deques with most preferred candidates on top
    voters = db.session.scalars(sa.select(Voter).where(Voter.ballot_id == ballot_id)).fetchall()
    rankings = [deque(int(entry) for entry in reversed(voter.vote.split(" "))) for voter in voters]

    if len(rankings) == 0:
        result = 'No votes have been cast yet'
        return render_template('results.html', result=result, ballot_opts=ballot_opts)

    win_threshold = len(rankings) / 2
    # print(rankings)
    # candidates points are stored as a dictionary of id keys and vote deque array values
    # points are determined by the length of these arrays
    cands = db.session.scalars(sa.select(Entry).where(Entry.ballot_id == ballot_id)).fetchall()
    cand_pts = {cand.id: [] for cand in cands}
    for ranking in rankings:
        cand_pts[ranking.pop()].append(ranking)

    rounds_df = pd.DataFrame({'Candidate IDs': [cand.id for cand in cands],
                              'Candidate Name': [cand.name for cand in cands]})
    round_num = 1

    while True:
        cand_results = list(cand_pts.items())
        cand_results.sort(key=lambda tup: len(tup[1]), reverse=True)

        extract_round_data(cand_pts, rounds_df, round_num)

        if len(cand_results[0][1]) > win_threshold:
            # the top candidate got more than 50% of the vote
            result = db.session.scalar(sa.select(Entry.name).where(Entry.id == cand_results[0][0]))
            break
        else:
            elim_threshold = len(cand_results[-1][1])
            elim_count = 0

            for cand in reversed(cand_results):
                if len(cand[1]) > elim_threshold:
                    break
                elim_count += 1

            if elim_count == len(cand_results):
                # the remaining candidates have the same number of votes
                # print('its a tie')
                result_list = db.session.scalars(
                    sa.select(Entry.name).where(Entry.id.in_(
                        [cand[0] for cand in
                         itertools.islice(cand_results, len(cand_results) - elim_count, len(cand_results))])))
                result = ", ".join(result_list)
                break
            else:
                for cand in itertools.islice(cand_results, len(cand_results) - elim_count, len(cand_results)):
                    for ranking in cand_pts.pop(cand[0]):
                        if ranking[-1] in cand_pts:
                            cand_pts[ranking.pop()].append(ranking)
        round_num += 1

    # splitting record votes and replacing with cand names for use in html
    cand_dict = {}
    for cand in cands:
        cand_dict[str(cand.id)] = cand.name
    for record in voters:
        record.vote = [cand_dict[cand] for cand in record.vote.split(" ")]

    json_plots = plot_rounds(rounds_df, round_num, win_threshold)

    return render_template('results.html',
                           result=result, records=voters, ballot_opts=ballot_opts, json_plots=json_plots)


def extract_round_data(cand_pts, rounds_df, round_num):
    """Along with candidate name and ID, rounds_df adds a column for each round's first-choice vote totals."""
    rounds_df['Round ' + str(round_num) + ' First-Choice Votes'] = [len(cand_pts.get(cand_id, []))
                                                                    for cand_id in rounds_df['Candidate IDs']]


def plot_rounds(rounds_df, round_count, win_threshold):
    json_plots = []
    max_votes = rounds_df['Round ' + str(round_count) + ' First-Choice Votes'].max()
    for i in range(1, round_count + 1):
        fig = px.bar(rounds_df, x='Candidate Name', y='Round ' + str(i) + ' First-Choice Votes')

        fig.add_hline(y=win_threshold, line_dash="dash", line_color="red", annotation_text="Win Threshold",
                      annotation_position="top left")
        fig = fig.update_layout(yaxis_tickmode='linear', yaxis_range=[0, max_votes])

        json_plots.append(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

    return json_plots
