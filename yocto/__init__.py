import os
import json

from flask import Flask

import yocto.config as config

def create_app(configType=None):
    app = Flask(__name__)
    
    app.config.from_object(getattr(config, configType, config.DevelopmentConfig))
    if not app.config["DEBUG"]:
        app.config.from_file(os.getenv("SECRET_KEY_PATH", f"{app.instance_path}/secret_key.json"), load=json.load, silent=False)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Import pages blueprint
    from yocto import pages, short
    app.register_blueprint(short.bp)
    app.register_blueprint(pages.bp)

    # Import database functions and initialize
    from yocto import db
    db.init_app(app)

    return app
