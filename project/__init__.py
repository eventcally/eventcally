import logging
import os
import sys
from datetime import timedelta

from flask import Flask, url_for
from flask_gzip import Gzip
from flask_mail import email_dispatched
from flask_security import Security, SQLAlchemySessionUserDatastore, user_registered
from werkzeug.routing.exceptions import BuildError

from project.custom_session_interface import CustomSessionInterface
from project.extensions import babel, cors, csrf, db, limiter, mail, migrate, security


def getenv_bool(name: str, default: str = "False"):
    return os.getenv(name, default).lower() in ("true", "1", "t")


def set_env_to_app(app: Flask, key: str, default: str = None):
    if key in os.environ and os.environ[key]:  # pragma: no cover
        app.config[key] = os.environ[key]
        return

    if default:
        app.config[key] = default


def load_app_config_from_env(app: Flask):
    # Load configuration from environment
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["REDIS_URL"] = os.getenv("REDIS_URL")
    app.config["LIMITER_REDIS_URL"] = os.getenv("LIMITER_REDIS_URL")
    app.config["SECURITY_EMAIL_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
    app.config["SERVER_NAME"] = os.getenv("SERVER_NAME")
    app.config["DOCS_URL"] = os.getenv("DOCS_URL")
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = getenv_bool(
        "ADMIN_UNIT_CREATE_REQUIRES_ADMIN"
    )
    app.config["SEO_SITEMAP_PING_GOOGLE"] = getenv_bool(
        "SEO_SITEMAP_PING_GOOGLE", "False"
    )
    app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY")
    set_env_to_app(app, "SITE_NAME", "EventCally")
    app.config["FLASK_DEBUG"] = getenv_bool("FLASK_DEBUG", "False")
    app.config["API_READ_ANONYM"] = getenv_bool("API_READ_ANONYM", "False")

    if os.getenv("PREFERRED_URL_SCHEME"):  # pragma: no cover
        app.config["PREFERRED_URL_SCHEME"] = os.getenv("PREFERRED_URL_SCHEME")

        if app.config["PREFERRED_URL_SCHEME"] == "https":
            app.config["SESSION_COOKIE_SECURE"] = True
            app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
            app.config["REMEMBER_COOKIE_SECURE"] = True
            app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

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

    # Mail configuration
    mail_server = os.getenv("MAIL_SERVER")

    if not mail_server:
        app.config["MAIL_SUPPRESS_SEND"] = True
        app.config["MAIL_DEFAULT_SENDER"] = "test@eventcally.com"
    else:  # pragma: no cover
        app.config["MAIL_SUPPRESS_SEND"] = False
        app.config["MAIL_SERVER"] = mail_server
        app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
        app.config["MAIL_USE_TLS"] = getenv_bool("MAIL_USE_TLS", "True")
        app.config["MAIL_USE_SSL"] = getenv_bool("MAIL_USE_SSL", "False")
        app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
        app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
        app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    if getenv_bool("TESTING"):  # pragma: no cover
        import project.cli.test

        app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}


def load_app_config_from_sys(app: Flask):
    if "celery" in sys.argv[0]:  # pragma: no cover
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 60,
            "pool_pre_ping": True,
        }


def create_app(config_override: dict | None = None) -> Flask:
    """Application factory function."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECURITY_CONFIRMABLE"] = True
    app.config["SECURITY_POST_LOGIN_VIEW"] = "manage_after_login"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = True
    app.config["SECURITY_RECOVERABLE"] = True
    app.config["SECURITY_CHANGEABLE"] = True
    app.config["BABEL_DEFAULT_LOCALE"] = "de"
    app.config["BABEL_DEFAULT_TIMEZONE"] = "Europe/Berlin"
    app.config["LANGUAGES"] = ["en", "de"]
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False

    load_app_config_from_env(app)
    load_app_config_from_sys(app)

    if config_override:
        app.config.update(config_override)

    # if app.config["FLASK_DEBUG"]:
    #     logging.basicConfig(level=logging.DEBUG)
    #     logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    #     logging.getLogger("authlib").setLevel(logging.DEBUG)

    from project.reverse_proxied import ReverseProxied

    app.wsgi_app = ReverseProxied(app.wsgi_app, app.config["PREFERRED_URL_SCHEME"])

    # Celery
    task_always_eager = "REDIS_URL" not in app.config or not app.config["REDIS_URL"]
    app.config.update(
        CELERY_CONFIG={
            "broker_url": app.config["REDIS_URL"],
            "result_backend": app.config["REDIS_URL"],
            "result_expires": timedelta(hours=1),
            "timezone": "Europe/Berlin",
            "broker_transport_options": {
                "queue_order_strategy": "priority",
                "priority_steps": list(range(3)),
                "sep": ":",
                "queue_order_strategy": "priority",
            },
            "task_default_priority": 1,  # 0=high, 1=normal, 2=low priority
            "task_always_eager": task_always_eager,
        }
    )

    from project.celery_init import init_celery

    init_celery(app)

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

    # Initialize extensions
    # Flask-Gzip doesn't support init_app pattern, create it directly
    Gzip(app)

    from project.i10n import get_locale, get_locale_from_request

    babel.init_app(app, locale_selector=get_locale)

    cors.init_app(
        app,
        resources={r"/.well-known/*", r"/api/*", r"/oauth/*", "/swagger/"},
    )

    csrf.init_app(app)
    mail.init_app(app)

    if app.config["MAIL_SUPPRESS_SEND"]:

        def log_message(message, app):
            app.logger.info(message.subject)
            app.logger.info(message.body)

        email_dispatched.connect(log_message, weak=False)

    # Database
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=False)

    # Rate limiting
    limiter.init_app(app)

    # Celery tasks - import to register tasks
    from project import base_tasks, celery_tasks

    # JSON provider
    from project.jsonld import CustomJsonProvider

    app.json_provider_class = CustomJsonProvider

    from project.forms.security import (
        ExtendedConfirmRegisterForm,
        ExtendedForgotPasswordForm,
        ExtendedLoginForm,
    )

    # Setup Flask-Security
    from project.models import Role, User

    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    security.init_app(
        app,
        user_datastore,
        confirm_register_form=ExtendedConfirmRegisterForm,
        login_form=ExtendedLoginForm,
        forgot_password_form=ExtendedForgotPasswordForm,
    )
    app.session_interface = CustomSessionInterface()

    # Signal handlers
    @user_registered.connect_via(app)
    def user_registered_sighandler(
        sender, user, confirm_token, confirmation_token, form_data
    ):
        if "accept_tos" in form_data and form_data["accept_tos"]:
            from project.services.user import set_user_accepted_tos

            set_user_accepted_tos(user)
            db.session.commit()

        if not user.locale:
            user.locale = get_locale_from_request()
            db.session.commit()

    # OAuth2
    from project.oauth2 import config_oauth

    config_oauth(app)

    # Initialize REST API (must happen before container.wire() imports api modules)
    from project.api import init_api

    init_api(app)

    # Dependency Injection Container
    from project.container import Application

    container = Application()
    container.config.from_dict(app.config)
    container.wire(
        packages=[
            "project.views",
            "project.api",
        ],
        warn_unresolved=True,
    )

    # Make container available in Flask app
    app.container = container

    # Command line
    import project.cli.cache
    import project.cli.data
    import project.cli.dump
    import project.cli.event
    import project.cli.seo
    import project.cli.user
    from project import init_data, jinja_filters, requests

    # Routes
    from project.views import (
        admin,
        admin_blueprint,
        admin_unit_member_invitation,
        custom_widget,
        dump,
        event,
        event_date,
        flask_admin,
        image,
        js,
        manage,
        manage_admin_unit,
        manage_blueprint,
        oauth,
        organization,
        organizer,
        planning,
        reference,
        reference_request,
        root,
    )
    from project.views import user as user_view
    from project.views import user_blueprint, verification_request, widget

    # Register blueprints
    from project.views.admin_blueprint import admin_bp
    from project.views.main_blueprint import main_bp
    from project.views.manage_admin_unit import manage_admin_unit_bp
    from project.views.manage_blueprint import manage_bp
    from project.views.user_blueprint import user_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(manage_bp)
    app.register_blueprint(manage_admin_unit_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(main_bp)

    # Initialize Jinja filters and context processors
    from project.jinja_filters import init_jinja_filters

    init_jinja_filters(app)

    # Initialize Flask-Admin
    from project.views.flask_admin import init_admin

    init_admin(app)

    # Register OAuth2 scheme handler
    from project.init_data import register_oauth2_scheme_once

    register_oauth2_scheme_once(app)

    # Register request hooks
    from project.requests import init_requests

    init_requests(app)

    # Register CLI command groups
    from project.cli.cache import cache_cli
    from project.cli.data import data_cli
    from project.cli.dump import dump_cli
    from project.cli.event import event_cli
    from project.cli.seo import seo_cli
    from project.cli.user import user_cli

    app.cli.add_command(cache_cli)
    app.cli.add_command(data_cli)
    app.cli.add_command(dump_cli)
    app.cli.add_command(event_cli)
    app.cli.add_command(seo_cli)
    app.cli.add_command(user_cli)

    if getenv_bool("TESTING"):  # pragma: no cover
        from project.cli.test import test_cli

        app.cli.add_command(test_cli)

    return app


# Cache paths - defined at module level for backward compatibility
cache_env = os.environ.get("CACHE_PATH", "tmp")
cache_path = (
    cache_env if os.path.isabs(cache_env) else os.path.join(os.getcwd(), cache_env)
)
dump_path = os.path.join(cache_path, "dump")
dump_org_path = os.path.join(cache_path, "dump_org")
img_path = os.path.join(cache_path, "img")
sitemap_file = "sitemap.xml"
robots_txt_file = "robots.txt"
sitemap_path = os.path.join(cache_path, sitemap_file)
robots_txt_path = os.path.join(cache_path, robots_txt_file)


if __name__ == "__main__":  # pragma: no cover
    app = create_app()
    app.run()
