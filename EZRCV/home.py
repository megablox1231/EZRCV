from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from EZRCV import db
import sqlalchemy as sa
from EZRCV.models import Ballot, Entry, Voter

bp = Blueprint('home', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        if 'vote' in request.form:
            return redirect(url_for('home.vote', ballot_id=request.form['voteCode']))
        elif 'results' in request.form:
            pass

    return render_template('index.html')


@bp.route('/create', methods=('GET', 'POST'))
def create_ballot():
    if request.method == "POST":
        name = request.form['name']
        entries = request.form.getlist('entries')

        ballot = Ballot(name=name)
        db.session.add(ballot)
        db.session.flush()
        for entry in entries:
            db.session.add(Entry(ballot_id=ballot.id, name=entry))
        db.session.commit()

        return render_template('index.html')
        # TODO: return render template that gives voting url

    return render_template('create-ballot.html')


@bp.route('/<int:ballot_id>/vote', methods=('GET', 'POST'))
def vote(ballot_id):
    if request.method == "POST":
        entry_ids = request.form.getlist('entry_ids')
        rankings = " ".join(ballot_id for ballot_id in entry_ids)
        db.session.add(Voter(ballot_id=ballot_id, vote=rankings))
        db.session.commit()

    entries = db.session.execute(sa.select(Entry).where(Entry.ballot_id == ballot_id))
    ballot_info = db.session.scalar(sa.select(Ballot).where(Ballot.id == ballot_id))
    return render_template('vote.html', entries=entries, ballot=ballot_info)
