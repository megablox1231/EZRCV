import pytest
from EZRCV import create_app, db


@pytest.fixture
def app():
    app = create_app('test_config.py')

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
