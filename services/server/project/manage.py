import configparser
import os
import sys
import socketio

from flask import Flask
from flask_socketio import SocketIO

global app
global sio


def create_app(config) -> Flask:
    app = Flask(__name__, template_folder='../../client/public',
                static_folder='../../client/public/static')

    app_section = config['app']
    app.config['DEBUG'] = app_section.getboolean('debug')
    app.port = app_section['port']
    app.host = app_section['host']

    app.config["database_url"] = config["database"]["url"]

    app.secret_key = app_section['secret'].encode()

    return app


def write_config_sample():
    config = configparser.ConfigParser()
    config["app"] = {}
    config["app"]["host"] = "0.0.0.0"
    config["app"]["port"] = "5000"
    config["app"]["debug"] = "true"
    config["app"]["secret"] = str(os.urandom(24))
    config["database"]["url"] = "sqlite:///storage/database.db"

    with open("config.ini", "w+") as f:
        config.write(f)


def init():
    global app
    global sio

    config_file = os.getenv('CONFIG_FILE', 'config.ini')

    config_parser = configparser.ConfigParser()
    if not config_parser.read(config_file):
        print('Error reading config.ini. Please edit the automatically generated config.ini to match desired settings.')
        write_config_sample()
        sys.exit(1)

    app = create_app(config_parser)
    sio = SocketIO(app, async_mode='gevent')

    # Setup blueprints
    from project.api import api
    app.register_blueprint(api)

    # Setup routes
    import project.views.index  # noqa
    import project.socket  # noqa

    import project.database.models

    # Import database and set it up.
    import project.database
    project.database.register_teardown(app)
    print("Attempting to connect to", app.config["database_url"])
    project.database.init_db(app.config["database_url"])

    # Create model
    project.database.metadata_create_all()

    print("Done initializing.")


init()
