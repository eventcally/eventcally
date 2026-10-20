import os
from datetime import timedelta

from flask import Flask

from project.shared.feature_flags import apply_feature_flags_to_config


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
    if app.config["LIMITER_REDIS_URL"]:
        app.config["RATELIMIT_STORAGE_URI"] = app.config["LIMITER_REDIS_URL"]
    app.config["SECURITY_EMAIL_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
    app.config["SERVER_NAME"] = os.getenv("SERVER_NAME")
    app.config["DOCS_URL"] = os.getenv("DOCS_URL")
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = getenv_bool(
        "ADMIN_UNIT_CREATE_REQUIRES_ADMIN"
    )
    app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY")
    app.config["VITE_DEV_SERVER_URL"] = os.getenv("VITE_DEV_SERVER_URL", "")
    set_env_to_app(app, "SITE_NAME", "EventCally")
    app.config["FLASK_DEBUG"] = getenv_bool("FLASK_DEBUG", "False")
    app.config["API_READ_ANONYM"] = getenv_bool("API_READ_ANONYM", "False")
    apply_feature_flags_to_config(app.config, os.getenv("FEATURE_FLAGS"))

    # Docker image tag names (comma-separated) baked into the image at build
    # time (see Dockerfile build-arg populated by the docker-build-push workflow).
    app.config["APP_TAGS"] = os.getenv("APP_TAGS", "")

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

    app.config["ENABLE_TEST_CLI"] = getenv_bool("TESTING")

    if getenv_bool("TESTING"):  # pragma: no cover
        app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}


def pin_db_session_timezone(app: Flask):
    # Pin the Postgres session timezone so timestamptz values are returned with
    # the same offset in every environment, regardless of the server default.
    engine_options = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {})
    connect_args = dict(engine_options.get("connect_args") or {})
    options = connect_args.get("options", "")

    if "timezone=" not in options:
        connect_args["options"] = f"{options} -c timezone=UTC".strip()

    engine_options["connect_args"] = connect_args
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options


def apply_defaults(app: Flask):
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


def celery_config(app: Flask) -> dict:
    task_always_eager = "REDIS_URL" not in app.config or not app.config["REDIS_URL"]
    return {
        "broker_url": app.config["REDIS_URL"],
        "result_backend": app.config["REDIS_URL"],
        "result_expires": timedelta(hours=1),
        "timezone": "Europe/Berlin",
        "broker_transport_options": {
            "queue_order_strategy": "priority",
            "priority_steps": list(range(3)),
            "sep": ":",
        },
        "task_default_priority": 1,  # 0=high, 1=normal, 2=low priority
        "task_always_eager": task_always_eager,
    }


def load_config(app: Flask, config_override: dict | None = None):
    """Defaults, then environment, then the override, then the timezone pin."""
    apply_defaults(app)
    load_app_config_from_env(app)

    if config_override:
        app.config.update(config_override)

    pin_db_session_timezone(app)
    app.config["CELERY_CONFIG"] = celery_config(app)
