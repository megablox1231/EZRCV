import sqlalchemy as sa
from EZRCV import db


def test_db_connection(app):
    with app.app_context():
        db.session.execute(sa.text('SELECT 1'))
