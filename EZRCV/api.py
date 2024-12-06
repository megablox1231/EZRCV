from flask import (
    Blueprint, redirect, render_template, request, url_for, flash
)
from EZRCV import db
from EZRCV import models
from EZRCV.models import Ballot, Entry, Voter


bp = Blueprint('api', __name__)


@bp.route('/ballot_info/<int:ballot_id>')
def get_ballot_info(ballot_id):
    return db.get_or_404(Ballot, ballot_id).to_dict()


@bp.route('/ballot_results/<int:ballot_id>')
def get_ballot_results(ballot_id):
    results = models.calculate_winners(ballot_id)

    # no votes cast yet
    if len(results) == 1:
        return None

    return {
        "result": results["result"]
    }
