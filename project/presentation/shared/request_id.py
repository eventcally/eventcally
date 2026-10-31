import re
import uuid

from flask import Flask, g, request

from project.infrastructure.logging_config import bind_log_context, reset_log_context

REQUEST_ID_HEADER = "X-Request-ID"

_valid_request_id = re.compile(r"[A-Za-z0-9._-]{1,128}")


def init_request_id(app: Flask):
    """Every request gets an id (taken from a well-formed `X-Request-ID` header or
    generated) that is echoed in the response and added to every log line of the
    request."""

    @app.before_request
    def _set_request_id():
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        g.request_id = (
            incoming if _valid_request_id.fullmatch(incoming) else uuid.uuid4().hex
        )
        g.request_log_context = bind_log_context(request_id=g.request_id)

    @app.after_request
    def _echo_request_id(response):
        request_id = g.get("request_id")
        if request_id:
            response.headers.setdefault(REQUEST_ID_HEADER, request_id)
        return response

    @app.teardown_request
    def _reset_request_log_context(exc):
        tokens = g.pop("request_log_context", None)
        if tokens:
            reset_log_context(tokens)
