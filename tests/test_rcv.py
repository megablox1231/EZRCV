import pytest
from EZRCV import db
from EZRCV.models import Ballot, Entry, Voter


@pytest.mark.parametrize('form, key', [('vote', 'voteCode'), ('results', 'resultsCode')])
def test_index(client, form, key):
    assert client.get('/').status_code == 200
    assert client.post('/', data={form: '', key: '1'}).status_code == 302


# Tests both create_ballot view and create_ballot_success view
def test_create_ballot(client, app):
    assert client.get('/create').status_code == 200
    response = client.post('/create', data={'name': 'election',
                                            'entries': ['Lucas', 'Claus', 'Kuma', 'Duster']}, follow_redirects=True)
    assert b'/3/vote' in response.data

    with app.app_context():
        assert db.session.query(Ballot).count() == 3
        assert db.session.query(Entry).where(Entry.ballot_id == 3).count() == 4


# Tests both vote view and vote_success view
def test_vote(client, app):
    assert client.get('/1/vote').status_code == 200
    response = client.post('/1/vote', data={'entry_ids': ['2', '1']}, follow_redirects=True)
    assert b'/1/results' in response.data

    with app.app_context():
        assert db.session.query(Voter).count() == 4


def test_win_results(client):
    response = client.get('/1/results')

    assert response.status_code == 200
    assert b'Ed' in response.data


def test_tie_results(client):
    client.post('/1/vote', data={'entry_ids': ['2', '1']})
    response = client.get('/1/results')

    assert response.status_code == 200
    assert b'Ed, Al' in response.data


def test_no_results(client):
    response = client.get('/2/results')

    assert response.status_code == 200
    assert b'No votes have been cast yet' in response.data
