import os
from flask import Flask, url_for, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import (
    Security,
    SQLAlchemySessionUserDatastore,
)
from flask_babelex import Babel
from flask_cors import CORS
from flask_qrcode import QRcode
from flask_mail import Mail, email_dispatched
from flask_migrate import Migrate
from flask_gzip import Gzip
from webargs import flaskparser

# Create app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECURITY_CONFIRMABLE"] = False
app.config["SECURITY_TRACKABLE"] = True
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config["SECURITY_RECOVERABLE"] = True
app.config["SECURITY_CHANGEABLE"] = True
app.config["SECURITY_EMAIL_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["LANGUAGES"] = ["en", "de"]

# Generate a nice key using secrets.token_urlsafe()
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw"
)
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get(
    "SECURITY_PASSWORD_SALT", "146585145368132386173505678016728509634"
)

# Gzip
gzip = Gzip(app)

# Cache pathes
cache_env = os.environ.get("CACHE_PATH", "tmp")
cache_path = (
    cache_env if os.path.isabs(cache_env) else os.path.join(app.root_path, cache_env)
)
dump_path = os.path.join(cache_path, "dump")
img_path = os.path.join(cache_path, "img")

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
        print(message.subject)
        print(message.body)

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

# Setup Flask-Security
from project.models import User, Role
from project.forms.security import ExtendedRegisterForm

user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

# OAuth2
from project.oauth2 import config_oauth

config_oauth(app)

# Init misc modules

from project import i10n
from project import jinja_filters
from project import init_data

# Routes
from project.views import (
    admin,
    admin_unit,
    admin_unit_member,
    admin_unit_member_invitation,
    api,
    event,
    event_date,
    event_place,
    event_suggestion,
    dump,
    image,
    manage,
    organizer,
    oauth,
    oauth2_client,
    oauth2_token,
    planing,
    reference,
    reference_request,
    reference_request_review,
    root,
    user,
    widget,
)

# API Resources
import project.api

# Command line
import project.cli.event
import project.cli.dump
import project.cli.user

if __name__ == "__main__":  # pragma: no cover
    app.run()
