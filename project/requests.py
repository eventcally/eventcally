from datetime import datetime, timedelta

from flask import g, request
from flask_login.utils import encode_cookie

from project import app


@app.after_request
def set_manage_admin_unit_cookie(response):
    admin_unit = getattr(g, "manage_admin_unit", None)

    if admin_unit:
        encoded = encode_cookie(str(admin_unit.id))
        response.set_cookie(
            "manage_admin_unit_id",
            value=encoded,
            expires=datetime.utcnow() + timedelta(days=365),
            secure=app.config["SESSION_COOKIE_SECURE"],
            samesite=app.config["SESSION_COOKIE_SAMESITE"],
        )

    return response


@app.after_request
def set_response_headers(response):
    if request and request.endpoint:
        if request.endpoint != "static" and request.endpoint != "widget_event_dates":
            response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers[
        "Content-Security-Policy"
    ] = "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-eval' 'unsafe-inline'; img-src 'self' data: *.openstreetmap.org;"
    return response
