import os
from base64 import b64decode
from flask import jsonify, Flask, render_template, request, url_for, redirect, abort, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import asc, func
from sqlalchemy import and_, or_, not_, event
from flask_security import Security, current_user, auth_required, roles_required, SQLAlchemySessionUserDatastore
from flask_security.utils import FsPermNeed
from flask_babelex import Babel, gettext, lazy_gettext, format_datetime, to_user_timezone
from flask_principal import Permission
from flask_cors import CORS
import pytz
import json
from flask_qrcode import QRcode
from flask_mail import Mail, Message, email_dispatched

# Create app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_EMAIL_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
app.config['LANGUAGES'] = ['en', 'de']
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

# Generate a nice key using secrets.token_urlsafe()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')

# i18n
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Europe/Berlin'
babel = Babel(app)

# cors
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# Mail
mail_server = os.getenv("MAIL_SERVER")

if mail_server is None:
    app.config['MAIL_SUPPRESS_SEND'] = True
    app.config['MAIL_DEFAULT_SENDER'] = 'test@oveda.de'
else:
    app.config['MAIL_SUPPRESS_SEND'] = False
    app.config['MAIL_SERVER'] = mail_server
    app.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
    app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", True)
    app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL", False)
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

if app.config['MAIL_SUPPRESS_SEND']:
    def log_message(message, app):
        print(message.subject)
        print(message.body)
    email_dispatched.connect(log_message)

# Create db
db = SQLAlchemy(app)

# qr code
QRcode(app)

# JSON
from project.jsonld import DateTimeEncoder
app.json_encoder = DateTimeEncoder

# Setup Flask-Security
from project.models import User, Role
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)

# OAuth
from project.oauth import blueprint
app.register_blueprint(blueprint, url_prefix="/login")

from project.i10n import *
from project.jinja_filters import *
from project.init_data import *

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
    image,
    manage,
    organizer,
    planing,
    reference,
    reference_request,
    reference_request_review,
    root,
    user,
    widget
)

if __name__ == '__main__':
    app.run()