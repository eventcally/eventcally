import datetime

from flask import g, redirect, request, url_for
from flask_login.utils import encode_cookie
from flask_security import current_user

from project import app


@app.after_request
def check_tos_accepted(response):
    if (
        response.status_code == 200
        and request.endpoint
        and not request.endpoint.startswith("api_")
        and not request.endpoint.startswith("widget_")
        and request.endpoint not in ["static", "user.accept_tos"]
        and current_user
        and current_user.is_authenticated
        and not current_user.tos_accepted_at
    ):
        return redirect(url_for("user.accept_tos", next=request.url))

    return response


@app.after_request
def set_manage_admin_unit_cookie(response):
    admin_unit = getattr(g, "manage_admin_unit", None)

    if admin_unit:
        encoded = encode_cookie(str(admin_unit.id))
        response.set_cookie(
            "manage_admin_unit_id",
            value=encoded,
            expires=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365),
            secure=app.config["SESSION_COOKIE_SECURE"],
            samesite=app.config["SESSION_COOKIE_SAMESITE"],
        )

    return response


@app.after_request
def set_response_headers(response):
    if request and request.endpoint:
        if request.endpoint.startswith("api_"):
            return response
        if (
            request.endpoint != "static"
            and request.endpoint != "widget_event_dates"
            and request.endpoint != "custom_widget_type"
        ):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-eval' 'unsafe-inline'; img-src 'self' blob: data: *.openstreetmap.org; connect-src 'self' blob: data:;"
    )
    return response
