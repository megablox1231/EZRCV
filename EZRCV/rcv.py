from flask import (
    Blueprint, redirect, render_template, request, url_for, flash
)

from EZRCV import models
from EZRCV import db
import sqlalchemy as sa
from EZRCV.models import Ballot, Entry, Voter

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
    """Returns the ballot results to the results template. Also passes on various ballot statistics."""
    result = models.calculate_winners(ballot_id)

    if len(result) == 1:
        winner = 'No votes have been cast yet'
        return render_template('results.html', result=winner, ballot_opts=result['ballot_opts'])

    result['result'] = ", ".join(result['result'])
    json_plots = plot_rounds(result['rounds_df'], result['round_num'], result['win_threshold'])

    return render_template('results.html', result=result['result'],
                           records=result['voters'], ballot_opts=result['ballot_opts'], json_plots=json_plots)


def plot_rounds(rounds_df, round_count, win_threshold):
    """Plots the results of each round of instant-runoff voting as plotly bar charts encoded to JSON."""
    json_plots = []
    max_votes = rounds_df['Round ' + str(round_count) + ' First-Choice Votes'].max()
    for i in range(1, round_count + 1):
        fig = px.bar(rounds_df, x='Candidate Name', y='Round ' + str(i) + ' First-Choice Votes')

        fig.add_hline(y=win_threshold, line_dash="dash", line_color="red", annotation_text="Win Threshold",
                      annotation_position="top left")
        fig = fig.update_layout(yaxis_tickmode='linear', yaxis_range=[0, max_votes+0.5], paper_bgcolor="rgba(0,0,0,0)",
                                font=dict(size=15))

        fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=2, linecolor='black')

        json_plots.append(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

    return json_plots
