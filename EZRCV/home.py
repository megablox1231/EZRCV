from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from EZRCV import db
import sqlalchemy as sa
from EZRCV.models import Ballot, Entry

bp = Blueprint('home', __name__)


@bp.route('/')
def index():
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


@bp.route('/vote', methods=('GET', 'POST'))
def vote():
    return render_template('vote.html')
