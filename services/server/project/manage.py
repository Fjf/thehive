import configparser
import os
import sys

from flask import Flask

global app


def create_app(config) -> Flask:
    app = Flask(__name__, template_folder='../../client/public',
                static_folder='../../client/public/static')

    print(app.template_folder)
    app_section = config['app']
    app.config['DEBUG'] = app_section.getboolean('debug')
    app.port = app_section['port']
    app.host = app_section['host']
    app.database_name = 'database.db'

    app.secret_key = app_section['secret'].encode()

    return app


def init():
    global app

    config_file = os.getenv('CONFIG_FILE', 'config.ini')

    config_parser = configparser.ConfigParser()
    if not config_parser.read(config_file):
        print('Error reading config.ini. Please copy config.ini.sample to '
              'config.ini and adjust it.')
        sys.exit(1)

    app = create_app(config_parser)

    # Setup blueprints
    # from api import api
    # app.register_blueprint(api)

    # Setup routes
    import project.views.index

    print("Done initializing.")


init()
