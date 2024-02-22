import os

from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__)
    # Default config
    app.config.from_mapping(
        SECRET_KEY='dev',
        TESTING=False,
        DATABASE="yocto",
    )

    if test_config is None:
        # Instance config if exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Test config, when testing
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Import pages blueprint
    from yocto import pages
    app.register_blueprint(pages.bp)

    # Import database functions and initialize
    from yocto import db
    db.init_app(app)

    return app
