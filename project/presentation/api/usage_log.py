"""API usage log: one record per `/api/` request on the logger `eventcally.api_usage`
(through the root handlers, so one JSON line with `LOG_FORMAT=json`), naming the
credential and the organization, app and user it belongs to.

`require_api_access` remembers what it resolved on `g.api_usage_auth`, so writing the
record needs no extra queries. Secrets never go into the record: header values are
not read, and the values of token-like query arguments are redacted.
"""

import logging
from dataclasses import asdict, dataclass
from functools import wraps
from time import perf_counter
from typing import Optional
from urllib.parse import urlencode

from flask import Flask, current_app, g, request
from flask_limiter.util import get_remote_address

from project.infrastructure.logging_config import API_USAGE_LOGGER

API_PATH_PREFIX = "/api/"
MAX_PATH_LENGTH = 2048
MAX_USER_AGENT_LENGTH = 512
REDACTED = "[redacted]"
SECRET_QUERY_ARGS = {
    "access_token",
    "refresh_token",
    "token",
    "id_token",
    "client_secret",
    "client_assertion",
    "assertion",
    "api_key",
    "apikey",
    "x-api-key",
    "code",
    "password",
}


@dataclass
class ApiUsageAuth:
    auth: str = "none"
    token_id: Optional[int] = None
    client_id: Optional[str] = None
    app_id: Optional[int] = None
    app_installation_id: Optional[int] = None
    user_id: Optional[int] = None
    api_key_id: Optional[int] = None
    admin_unit_id: Optional[int] = None
    rate_limit_key: Optional[str] = None


def _usage_log_enabled() -> bool:
    return current_app.config["API_USAGE_LOG"]


def _remembering(func):
    """Only when the usage log is on, and never breaks the request."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if _usage_log_enabled():
                func(*args, **kwargs)
        except Exception:
            current_app.logger.exception("Could not remember the API usage auth")

    return wrapper


@_remembering
def remember_token_auth(token):
    app_id = token.app_id

    if token.app_installation_id:
        # Installation tokens name only the installation; it knows the app.
        app_installation = token.app_installation
        app_id = app_id or app_installation.oauth2_client_id
        admin_unit_id = app_installation.admin_unit_id
    else:
        admin_unit_id = token.client.admin_unit_id

    g.api_usage_auth = ApiUsageAuth(
        auth="oauth2",
        token_id=token.id,
        client_id=token.client_id,
        app_id=app_id,
        app_installation_id=token.app_installation_id,
        user_id=token.user_id,
        admin_unit_id=admin_unit_id,
        rate_limit_key=token.get_rate_limit_key(),
    )


@_remembering
def remember_api_key_auth(api_key):
    g.api_usage_auth = ApiUsageAuth(
        auth="api_key",
        api_key_id=api_key.id,
        user_id=api_key.user_id,
        admin_unit_id=api_key.admin_unit_id,
        rate_limit_key=api_key.get_rate_limit_key(),
    )


@_remembering
def remember_anonymous_auth():
    g.api_usage_auth = ApiUsageAuth(rate_limit_key=get_remote_address())


def _presented_auth() -> ApiUsageAuth:
    """What the client presented when authentication failed before anything was
    resolved. Only the presence of the headers is checked."""
    if request.headers.get("Authorization", "").startswith("Bearer "):
        return ApiUsageAuth(auth="oauth2")

    if request.headers.get("X-API-Key"):
        return ApiUsageAuth(auth="api_key")

    return ApiUsageAuth()


def _redacted_path() -> str:
    args = [
        (key, REDACTED if key.lower() in SECRET_QUERY_ARGS else value)
        for key, value in request.args.items(multi=True)
    ]
    path = f"{request.path}?{urlencode(args)}" if args else request.path
    return path[:MAX_PATH_LENGTH]


def build_api_usage_record(status: int) -> dict:
    auth = g.get("api_usage_auth") or _presented_auth()
    started = g.get("api_usage_started")

    return {
        "type": "api_usage",
        "request_id": g.get("request_id"),
        "method": request.method,
        "path": _redacted_path(),
        "endpoint": request.endpoint,
        "status": status,
        "duration_ms": (
            round((perf_counter() - started) * 1000) if started is not None else None
        ),
        "ip": get_remote_address(),
        "user_agent": request.user_agent.string[:MAX_USER_AGENT_LENGTH] or None,
        **asdict(auth),
    }


def _is_api_request() -> bool:
    return request.path.startswith(API_PATH_PREFIX)


def _write(status: int):
    try:
        if (
            not _usage_log_enabled()
            or not _is_api_request()
            or g.get("api_usage_logged")
        ):
            return

        g.api_usage_logged = True
        record = build_api_usage_record(status)
        # 5xx records also go to the error log (fluentd keeps level error)
        level = logging.ERROR if status >= 500 else logging.INFO
        logging.getLogger(API_USAGE_LOGGER).log(level, "api_usage", extra=record)
    except Exception:
        current_app.logger.exception("Could not write the API usage record")


def init_api_usage_log(app: Flask):
    @app.before_request
    def _start_api_usage():
        if _is_api_request():
            g.api_usage_started = perf_counter()

    @app.after_request
    def _write_api_usage(response):
        _write(response.status_code)
        return response

    @app.teardown_request
    def _write_api_usage_on_error(exc):
        # Exceptions that propagate skip after_request; record them as 500.
        if exc is not None:
            _write(500)
