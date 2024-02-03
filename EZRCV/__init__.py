import os
import sqlalchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
# from flask_migrate import Migrate


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        # load the instance config when not testing
        app.config.from_pyfile('config.py', silent=False)

    else:
        # load the test config if passed in
        app.config.from_pyfile(test_config)

    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy.URL.create(
        'mysql+mysqldb',
        username=app.config['USER'],
        password=app.config['PASSWORD'],
        host=app.config['HOST'],
        port=app.config['PORT'],
        database=app.config['DB_NAME']
    )

    # init database extension
    db.init_app(app)
    # migrate.init_app(app, db)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index')

    return app
