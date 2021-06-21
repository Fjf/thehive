import configparser
import os
import sys

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from project.bot import Bot
from project.database import create_all_models

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
    config["app"]["port"] = "5001"
    config["app"]["debug"] = "true"
    config["app"]["secret"] = str(os.urandom(24))
    config["database"] = {}
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

    CORS(app)

    # Setup blueprints
    from project.api import api
    app.register_blueprint(api)

    # Setup routes
    import project.views.index  # noqa
    import project.socket  # noqa

    # Import database and set it up.
    import project.database.models  # noqa
    import project.database  # noqa

    # Create model
    create_all_models()

    # Start ai move handler thread
    app.bot = Bot(app)
    app.bot.start()

    # Games holder
    app.games = {}

    print("Done initializing.")


init()
