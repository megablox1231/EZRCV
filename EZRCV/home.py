from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

bp = Blueprint('home', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/create', methods=('GET', 'POST'))
def create_ballot():
    if request.method == "POST":
        print(request.form['name'])

    return render_template('create-ballot.html')
