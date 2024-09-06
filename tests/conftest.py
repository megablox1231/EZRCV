import pytest
from EZRCV import create_app, db
from EZRCV.models import Ballot, Entry, Voter


@pytest.fixture
def app():
    app = create_app('test_config.py')

    with app.app_context():
        db.create_all()

        db.session.add(Ballot(name='ballot', display_records=True, allow_name=True))
        db.session.add(Entry(ballot_id=1, name='Ed'))
        db.session.add(Entry(ballot_id=1, name='Al'))
        db.session.add(Voter(ballot_id=1, name='Voter1', vote='1 2'))
        db.session.add(Voter(ballot_id=1, name='Voter2', vote='2 1'))
        db.session.add(Voter(ballot_id=1, name='Voter3', vote='1 2'))

        db.session.add(Ballot(name='noShow', display_records=False, allow_name=False))
        db.session.add(Entry(ballot_id=2, name='Ed'))
        db.session.add(Entry(ballot_id=2, name='Al'))

        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
