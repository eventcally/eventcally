import logging
import os

from flask import Flask, jsonify, redirect, request, url_for
from flask_babelex import Babel
from flask_cors import CORS
from flask_gzip import Gzip
from flask_mail import Mail, email_dispatched
from flask_migrate import Migrate
from flask_qrcode import QRcode
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_sqlalchemy import SQLAlchemy
from webargs import flaskparser

from project.custom_session_interface import CustomSessionInterface

# Create app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECURITY_CONFIRMABLE"] = True
app.config["SECURITY_POST_LOGIN_VIEW"] = "manage"
app.config["SECURITY_TRACKABLE"] = True
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_SEND_REGISTER_EMAIL"] = True
app.config["SECURITY_RECOVERABLE"] = True
app.config["SECURITY_CHANGEABLE"] = True
app.config["SECURITY_EMAIL_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["LANGUAGES"] = ["en", "de"]
app.config["SERVER_NAME"] = os.getenv("SERVER_NAME")

# Proxy handling
if os.getenv("PREFERRED_URL_SCHEME"):  # pragma: no cover
    app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME")

from project.reverse_proxied import ReverseProxied

app.wsgi_app = ReverseProxied(app.wsgi_app)

# Generate a nice key using secrets.token_urlsafe()
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw"
)
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get(
    "SECURITY_PASSWORD_SALT", "146585145368132386173505678016728509634"
)

# Gunicorn logging
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.hasHandlers():
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

# Gzip
gzip = Gzip(app)

# Cache pathes
cache_env = os.environ.get("CACHE_PATH", "tmp")
cache_path = (
    cache_env if os.path.isabs(cache_env) else os.path.join(app.root_path, cache_env)
)
dump_path = os.path.join(cache_path, "dump")
img_path = os.path.join(cache_path, "img")
sitemap_file = "sitemap.xml"
robots_txt_file = "robots.txt"
sitemap_path = os.path.join(cache_path, sitemap_file)
robots_txt_path = os.path.join(cache_path, robots_txt_file)

# i18n
app.config["BABEL_DEFAULT_LOCALE"] = "de"
app.config["BABEL_DEFAULT_TIMEZONE"] = "Europe/Berlin"
babel = Babel(app)

# cors
cors = CORS(app, resources={r"/api/*", "/swagger/"})

# Mail
mail_server = os.getenv("MAIL_SERVER")

if mail_server is None:
    app.config["MAIL_SUPPRESS_SEND"] = True
    app.config["MAIL_DEFAULT_SENDER"] = "test@oveda.de"
else:  # pragma: no cover
    app.config["MAIL_SUPPRESS_SEND"] = False
    app.config["MAIL_SERVER"] = mail_server
    app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", True)
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", False)
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

if app.config["MAIL_SUPPRESS_SEND"]:

    def log_message(message, app):
        app.logger.info(message.subject)
        app.logger.info(message.body)

    email_dispatched.connect(log_message)

# Create db
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# API
from project.api import RestApi

# qr code
QRcode(app)

# JSON
from project.jsonld import DateTimeEncoder

app.json_encoder = DateTimeEncoder

from project.forms.security import ExtendedConfirmRegisterForm

# Setup Flask-Security
from project.models import Role, User

user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(
    app, user_datastore, confirm_register_form=ExtendedConfirmRegisterForm
)
app.session_interface = CustomSessionInterface()

# OAuth2
from project.oauth2 import config_oauth

config_oauth(app)

# Init misc modules

# API Resources
import project.api

# Command line
import project.cli.dump
import project.cli.event
import project.cli.seo
import project.cli.user
from project import i10n, init_data, jinja_filters

# Routes
from project.views import (
    admin,
    admin_unit,
    admin_unit_member,
    admin_unit_member_invitation,
    api,
    dump,
    event,
    event_date,
    event_place,
    event_suggestion,
    image,
    manage,
    oauth,
    oauth2_client,
    oauth2_token,
    organizer,
    planing,
    reference,
    reference_request,
    reference_request_review,
    root,
    user,
    widget,
)

if __name__ == "__main__":  # pragma: no cover
    app.run()
