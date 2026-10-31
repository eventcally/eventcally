import logging
import os

from flask import Flask
from flask_gzip import Gzip
from flask_mail import email_dispatched
from flask_security import SQLAlchemySessionUserDatastore
from jinja2 import ChoiceLoader, FileSystemLoader
from werkzeug.middleware.proxy_fix import ProxyFix

from project.config import load_config
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

logger = logging.getLogger(__name__)


def _init_logging(app: Flask):
    from project.infrastructure.logging_config import init_logging

    # app.logger writes through the root handler (LOG_FORMAT), not Flask's default one
    app.logger.handlers = []
    app.logger.propagate = True
    init_logging()


def _init_extensions(app: Flask):
    from project.presentation.shared.i10n import get_locale

    # Flask-Gzip doesn't support init_app pattern, create it directly
    Gzip(app)
    babel.init_app(app, locale_selector=get_locale)
    cors.init_app(
        app,
        resources={r"/.well-known/*", r"/api/*", r"/oauth/*", "/swagger/"},
    )
    csrf.init_app(app)
    mail.init_app(app)
    mail.default_sender = app.config.get("MAIL_DEFAULT_SENDER")

    if app.config["MAIL_SUPPRESS_SEND"]:

        def log_message(app, message):
            logger.info(
                "Mail not sent (MAIL_SUPPRESS_SEND)",
                extra={
                    "recipients": message.recipients,
                    "subject": message.subject,
                    "body": message.body,
                },
            )

        email_dispatched.connect(log_message, weak=False)

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=False)
    limiter.init_app(app)


def _init_security(app: Flask):
    # The datastore needs the models, which the web channel may not import.
    from project.infrastructure.models import Role, User
    from project.presentation.web.forms.security import (
        ExtendedConfirmRegisterForm,
        ExtendedForgotPasswordForm,
        ExtendedLoginForm,
    )

    security.init_app(
        app,
        SQLAlchemySessionUserDatastore(db.session, User, Role),
        confirm_register_form=ExtendedConfirmRegisterForm,
        login_form=ExtendedLoginForm,
        forgot_password_form=ExtendedForgotPasswordForm,
    )
    app.session_interface = CustomSessionInterface()


def _init_oauth(app: Flask):
    # The model-backed server lives in infrastructure; presentation only holds the slots.
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


def _init_container(app: Flask):
    from project.container import Application

    container = Application()
    container.config.from_dict(app.config)
    container.wire(
        packages=[
            "project.presentation.web.views",
            "project.presentation.web.modular",
            "project.presentation.api",
            "project.presentation.bff",
        ],
        warn_unresolved=True,
    )

    @app.teardown_appcontext
    def remove_read_session(exception=None):
        # Safety net for reads that bypassed SqlAlchemyReadSessionScope.
        container.infrastructure.read_session().remove()

    return container


def create_app(config_override: dict | None = None) -> Flask:
    """Application factory function (the composition root)."""
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

    # Must be set before anything touches `app.json` (it is created lazily).
    from project.presentation.web.jsonld import CustomJsonProvider

    app.json_provider_class = CustomJsonProvider

    from project.infrastructure.celery_app import init_celery
    from project.infrastructure.reverse_proxied import ReverseProxied

    app.wsgi_app = ReverseProxied(app.wsgi_app, app.config["PREFERRED_URL_SCHEME"])
    # Rate limits key on the client IP, which the proxies pass in X-Forwarded-For.
    if app.config["PROXY_FIX_X_FOR"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["PROXY_FIX_X_FOR"])
    init_celery(app)
    _init_logging(app)
    _init_extensions(app)

    # Imported for the task registration and the beat schedule hook.
    import project.infrastructure.celery_base_tasks  # noqa: F401
    import project.presentation.tasks.celery_tasks  # noqa: F401

    _init_security(app)
    _init_oauth(app)

    from project.presentation.api import init_api, register_oauth2_scheme_once
    from project.presentation.bff import init_bff
    from project.presentation.cli import init_cli
    from project.presentation.shared.request_id import init_request_id
    from project.presentation.web import init_web
    from project.presentation.web.requests import init_requests

    # The REST API and the BFF must be initialized before container.wire() imports
    # their modules.
    init_request_id(app)
    init_api(app)
    init_bff(app)
    app.container = _init_container(app)

    # `before_request` order matters: web wiring, OAuth2 scheme, then request hooks.
    init_web(app)
    register_oauth2_scheme_once(app)
    init_requests(app)
    init_cli(app)

    return app
