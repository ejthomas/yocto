import os
import json

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

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

    # Set up reverse proxy if using nginx
    if os.getenv("NGINX_CONF"):
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    return app
