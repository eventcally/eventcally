from functools import wraps

from flask import current_app, flash, g, redirect, url_for
from flask_babel import format_date, format_time, gettext
from flask_security import current_user
from markupsafe import Markup
from psycopg2.errorcodes import UNIQUE_VIOLATION
from sqlalchemy.exc import SQLAlchemyError

from project.application.queries import GetSettingsQuery
from project.domain.errors import BaseError
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.presentation.shared.access import has_access
from project.presentation.shared.urls import url_for_image
from project.shared.utils import strings_are_equal_ignoring_case


def get_settings():
    """The site settings through the query bus (empty values without a row)."""
    return current_app.container.cqrs.query_bus().handle(GetSettingsQuery())


def handleSqlError(e: SQLAlchemyError) -> str:
    if not hasattr(e, "orig") or not e.orig:
        return str(e)

    prefix = None
    message = gettext(e.orig.message) if hasattr(e.orig, "message") else str(e.orig)

    if e.orig.pgcode == UNIQUE_VIOLATION:
        prefix = gettext(
            "An entry with the entered values ​​already exists. Duplicate entries are not allowed."
        )

    if not prefix:
        return message

    return "%s (%s)" % (prefix, message)


def handleBaseError(e: BaseError) -> str:
    message = gettext(e.message)

    if hasattr(e, "cause") and e.cause:
        if isinstance(e.cause, SQLAlchemyError):
            return handleSqlError(e.cause)

        detail = (
            gettext(e.cause.message) if hasattr(e.cause, "message") else str(e.cause)
        )
        return f"{message} ({detail})"

    return message  # pragma: no cover


def flash_errors(form, prefix=None):
    for field_name, errors in form.errors.items():
        field = getattr(form, field_name)
        field_label = field.label.text

        if prefix:
            field_label = f"{prefix} {field_label}"

        for error in errors:
            flash(
                gettext("Error in the %s field - %s") % (field_label, error),
                "danger",
            )


def flash_message(msg, url, link_text=None, category="success"):
    if not link_text:
        link_text = gettext("Show")
    link = ' &ndash; <a href="%s">%s</a>' % (url, link_text)
    message = Markup(msg + link)
    flash(message, category)


def permission_missing(redirect_location, message=None):
    if not message:
        message = gettext("You do not have permission for this action")

    flash(message, "danger")
    return redirect(redirect_location)


def truncate(data: str, length: int) -> str:
    if not data:
        return data

    return (data[: length - 2] + "..") if len(data) > length else data


def get_meta_data(event, event_date=None) -> dict:
    """Page meta of an event (read model) and optionally one of its dates."""
    meta = dict()
    meta["title"] = event.name

    if (
        event.attendance_mode
        and event.attendance_mode != EventAttendanceMode.online
        and event.event_place
    ):
        meta["title"] = f"{meta['title']} @ {event.event_place.name}"

        if event.event_place.location and event.event_place.location.city:
            meta["title"] = f"{meta['title']}, {event.event_place.location.city}"

    if event_date:
        date_str = format_date(event_date.start, "full")
        time_str = format_time(event_date.start, "short")
        meta["description"] = f"{date_str} {time_str}"

    if event.description:
        desc_short = truncate(event.description, 300)

        if "description" in meta:
            meta["description"] = f"{meta['description']}: {desc_short}"
        else:
            meta["description"] = desc_short

    if event.photo_id:
        meta["image"] = url_for_image(event.photo, _external=True)

    return meta


def get_invitation_access_result(email: str):
    from project.infrastructure.user_datastore import find_user_by_email

    # Wenn der aktuelle Nutzer nicht der Empfänger der Einladung ist, Meldung ausgeben
    if current_user.is_authenticated and not strings_are_equal_ignoring_case(
        email, current_user.email
    ):
        return permission_missing(
            url_for("main.profile"),
            gettext(
                "The invitation was issued to another user. Sign in with the email address the invitation was sent to."
            ),
        )

    # Wenn Email nicht als Nutzer vorhanden, dann direkt zu Registrierung
    if not find_user_by_email(email):
        return redirect(url_for("security.register"))

    # Wenn nicht angemeldet, dann zum Login
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()

    return None


def manage_permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_access(g.manage_admin_unit, permission):
                return permission_missing(
                    url_for("main.manage_admin_unit", id=g.manage_admin_unit.id)
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_docs_url(path: str, **kwargs):  # pragma: no cover
    base_url = current_app.config["DOCS_URL"]
    if not base_url:
        return None

    return f"{base_url}{path}"
