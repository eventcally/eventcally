import logging
import os
from datetime import timedelta

from flask import Flask
from flask_babelex import Babel
from flask_cors import CORS
from flask_gzip import Gzip
from flask_mail import Mail, email_dispatched
from flask_migrate import Migrate
from flask_qrcode import QRcode
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from project.custom_session_interface import CustomSessionInterface


def getenv_bool(name: str, default: str = "False"):  # pragma: no cover
    return os.getenv(name, default).lower() in ("true", "1", "t")


# Create app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["REDIS_URL"] = os.getenv("REDIS_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECURITY_CONFIRMABLE"] = True
app.config["SECURITY_POST_LOGIN_VIEW"] = "manage_after_login"
app.config["SECURITY_TRACKABLE"] = True
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_SEND_REGISTER_EMAIL"] = True
app.config["SECURITY_RECOVERABLE"] = True
app.config["SECURITY_CHANGEABLE"] = True
app.config["SECURITY_EMAIL_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["LANGUAGES"] = ["en", "de"]
app.config["SITE_NAME"] = os.getenv("SITE_NAME", "gsevpt")
app.config["SERVER_NAME"] = os.getenv("SERVER_NAME")
app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = os.getenv(
    "ADMIN_UNIT_CREATE_REQUIRES_ADMIN", False
)
app.config["SEO_SITEMAP_PING_GOOGLE"] = getenv_bool("SEO_SITEMAP_PING_GOOGLE", "False")

# Proxy handling
if os.getenv("PREFERRED_URL_SCHEME"):  # pragma: no cover
    app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME")

from project.reverse_proxied import ReverseProxied

app.wsgi_app = ReverseProxied(app.wsgi_app)

# Celery
task_always_eager = "REDIS_URL" not in app.config or not app.config["REDIS_URL"]
app.config.update(
    CELERY_CONFIG={
        "broker_url": app.config["REDIS_URL"],
        "result_backend": app.config["REDIS_URL"],
        "result_expires": timedelta(hours=1),
        "broker_pool_limit": None,
        "redis_max_connections": 2,
        "timezone": "Europe/Berlin",
        "broker_transport_options": {
            "max_connections": 2,
            "queue_order_strategy": "priority",
            "priority_steps": list(range(3)),
            "sep": ":",
            "queue_order_strategy": "priority",
        },
        "task_default_priority": 1,  # 0=high, 1=normal, 2=low priority
        "task_always_eager": task_always_eager,
    }
)


from project.celery import create_celery

celery = create_celery(app)

# Generate a nice key using secrets.token_urlsafe()
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw"
)
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get(
    "SECURITY_PASSWORD_SALT", "146585145368132386173505678016728509634"
)

app.config["JWT_PUBLIC_JWKS"] = os.environ.get("JWT_PUBLIC_JWKS", "")
app.config["JWT_PRIVATE_KEY"] = os.environ.get("JWT_PRIVATE_KEY", "").replace(
    r"\n", "\n"
)

# Gunicorn logging
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.hasHandlers():
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

# One line logging
from project.one_line_formatter import init_logger_with_one_line_formatter

init_logger_with_one_line_formatter(logging.getLogger())
init_logger_with_one_line_formatter(app.logger)

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
cors = CORS(
    app,
    resources={r"/.well-known/*", r"/api/*", r"/oauth/*", "/swagger/"},
)

# CRSF protection
csrf = CSRFProtect(app)
app.config["WTF_CSRF_CHECK_DEFAULT"] = False

# Mail
mail_server = os.getenv("MAIL_SERVER")

if not mail_server:
    app.config["MAIL_SUPPRESS_SEND"] = True
    app.config["MAIL_DEFAULT_SENDER"] = "test@gsevpt.de"
else:  # pragma: no cover
    app.config["MAIL_SUPPRESS_SEND"] = False
    app.config["MAIL_SERVER"] = mail_server
    app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
    app.config["MAIL_USE_TLS"] = getenv_bool("MAIL_USE_TLS", "True")
    app.config["MAIL_USE_SSL"] = getenv_bool("MAIL_USE_SSL", "False")
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

# Celery tasks
from project import celery_tasks

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
import project.cli.cache
import project.cli.dump
import project.cli.event
import project.cli.seo

if os.getenv("TESTING", False):  # pragma: no cover
    import project.cli.test

    app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}

import project.cli.user
from project import i10n, init_data, jinja_filters, requests

# Routes
from project.views import (
    admin,
    admin_unit,
    admin_unit_member,
    admin_unit_member_invitation,
    dump,
    event,
    event_date,
    event_place,
    event_suggestion,
    image,
    js,
    manage,
    oauth,
    oauth2_client,
    oauth2_token,
    organization,
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
