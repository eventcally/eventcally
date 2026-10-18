import logging
import os

from flask import Flask
from flask_gzip import Gzip
from flask_mail import email_dispatched
from flask_security import SQLAlchemySessionUserDatastore, user_registered
from jinja2 import ChoiceLoader, FileSystemLoader

from project.config import getenv_bool, load_config
from project.infrastructure.custom_session_interface import CustomSessionInterface
from project.infrastructure.extensions import (
    babel,
    cors,
    csrf,
    db,
    limiter,
    mail,
    migrate,
    security,
)


def create_app(config_override: dict | None = None) -> Flask:
    """Application factory function."""
    # The import name stays "project" (not `__name__`): it fixes `root_path` and
    # `celery.main`, which Celery derives task names and the default queue from.
    app = Flask(
        "project",
        template_folder="presentation/web/templates",
        static_folder="presentation/web/static",
    )
    # E-mail templates live outside the web channel: infrastructure renders them
    # (also from Celery), and they import the web macros (`_macros.html`).
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(os.path.join(app.root_path, "presentation/web/templates")),
            FileSystemLoader(os.path.join(app.root_path, "templates")),
        ]
    )
    load_config(app, config_override)

    from project.infrastructure.reverse_proxied import ReverseProxied

    app.wsgi_app = ReverseProxied(app.wsgi_app, app.config["PREFERRED_URL_SCHEME"])

    # Celery
    from project.infrastructure.celery_app import init_celery

    init_celery(app)

    # Gunicorn logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.hasHandlers():
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    # One line logging
    from project.infrastructure.one_line_formatter import (
        init_logger_with_one_line_formatter,
    )

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
    mail.default_sender = app.config.get("MAIL_DEFAULT_SENDER")

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
    import project.celery_tasks  # noqa: F401
    import project.infrastructure.celery_base_tasks  # noqa: F401

    # JSON provider
    from project.presentation.web.jsonld import CustomJsonProvider

    app.json_provider_class = CustomJsonProvider

    # Setup Flask-Security
    from project.infrastructure.models import Role, User
    from project.presentation.web.forms.security import (
        ExtendedConfirmRegisterForm,
        ExtendedForgotPasswordForm,
        ExtendedLoginForm,
    )

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
            from project.infrastructure.user_datastore import set_user_accepted_tos

            set_user_accepted_tos(user)
            db.session.commit()

        if not user.locale:
            user.locale = get_locale_from_request()
            db.session.commit()

    # OAuth2
    import project.presentation.shared.oauth2_extensions as oauth2_ext
    from project.infrastructure.oauth2_server import (
        create_authorization_server,
        create_bearer_token_validator_cls,
    )
    from project.presentation.shared.scopes import replace_legacy_scopes

    oauth2_ext.authorization = create_authorization_server(app, replace_legacy_scopes)
    oauth2_ext.require_oauth.register_token_validator(
        create_bearer_token_validator_cls()()
    )

    # Initialize REST API (must happen before container.wire() imports api modules)
    from project.presentation.api import init_api

    init_api(app)

    # Dependency Injection Container
    from project.container import Application

    container = Application()
    container.config.from_dict(app.config)
    container.wire(
        packages=[
            "project.presentation.web.views",
            "project.presentation.web.modular",
            "project.presentation.api",
        ],
        warn_unresolved=True,
    )

    # Make container available in Flask app
    app.container = container

    @app.teardown_appcontext
    def remove_read_session(exception=None):
        # Safety net for reads that bypassed SqlAlchemyReadSessionScope.
        container.infrastructure.read_session().remove()

    # Register blueprints
    from project.presentation.web.views.admin_blueprint import admin_bp
    from project.presentation.web.views.main_blueprint import main_bp
    from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
    from project.presentation.web.views.manage_blueprint import manage_bp
    from project.presentation.web.views.user_blueprint import user_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(manage_bp)
    app.register_blueprint(manage_admin_unit_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(main_bp)

    # Query handlers authorize the actor themselves; map their refusal to 401 for
    # views. API routes are handled by `RestApi.handle_error` first.
    from project.domain.errors.unauthorized_error import UnauthorizedError

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(error):
        from werkzeug.exceptions import Unauthorized

        return Unauthorized()

    # Initialize Jinja filters and context processors
    from project.presentation.web.jinja_filters import init_jinja_filters

    init_jinja_filters(app)

    # Initialize Flask-Admin
    from project.presentation.web.views.flask_admin import init_admin

    init_admin(app)

    # Register OAuth2 scheme handler
    from project.presentation.api import register_oauth2_scheme_once

    register_oauth2_scheme_once(app)

    # Register request hooks
    from project.presentation.web.requests import init_requests

    init_requests(app)

    # Register CLI command groups
    from project.presentation.cli.cache import cache_cli
    from project.presentation.cli.data import data_cli
    from project.presentation.cli.dump import dump_cli
    from project.presentation.cli.event import event_cli
    from project.presentation.cli.seo import seo_cli
    from project.presentation.cli.user import user_cli

    app.cli.add_command(cache_cli)
    app.cli.add_command(data_cli)
    app.cli.add_command(dump_cli)
    app.cli.add_command(event_cli)
    app.cli.add_command(seo_cli)
    app.cli.add_command(user_cli)

    if getenv_bool("TESTING"):  # pragma: no cover
        from project.presentation.cli.test import test_cli

        app.cli.add_command(test_cli)

    return app
