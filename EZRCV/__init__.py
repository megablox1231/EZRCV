import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        # load the instance config when not testing
        app.config.from_pyfile('config.py', silent=False)

        # app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy.URL.create(
        #     'mysql+mysqldb',
        #     username=app.config['USER'],
        #     password=app.config['PASSWORD'],
        #     host=app.config['HOST'],
        #     port=app.config['PORT'],
        #     database=app.config['DB_NAME']
        # )
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # init database extension
    # db.init_app(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index')

    return app
