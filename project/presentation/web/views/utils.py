from functools import wraps
from urllib.parse import quote_plus

from flask import current_app, flash, g, redirect, request, url_for
from flask_babel import format_date, format_time, gettext
from flask_security import current_user
from markupsafe import Markup
from psycopg2.errorcodes import UNIQUE_VIOLATION
from sqlalchemy.exc import SQLAlchemyError

from project.application.queries import GetSettingsQuery
from project.domain.errors import BaseError
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.presentation.shared.access import (
    get_admin_unit_for_manage_or_404,
    has_access,
)
from project.presentation.shared.current_admin_unit import set_current_admin_unit
from project.presentation.shared.urls import url_for_image
from project.shared.dateutils import berlin_tz, round_to_next_day
from project.shared.utils import get_place_str, strings_are_equal_ignoring_case


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


def get_pagination_urls(pagination, **kwargs):
    result = {}

    if pagination:
        result["page"] = pagination.page
        result["pages"] = pagination.pages
        result["total"] = pagination.total

        if pagination.has_prev:
            args = request.args.copy()
            args.update(kwargs)
            args["page"] = pagination.prev_num
            result["prev_url"] = url_for(request.endpoint, **args)
            args["page"] = 1
            result["first_url"] = url_for(request.endpoint, **args)

        if pagination.has_next:
            args = request.args.copy()
            args.update(kwargs)
            args["page"] = pagination.next_num
            result["next_url"] = url_for(request.endpoint, **args)
            args["page"] = pagination.pages
            result["last_url"] = url_for(request.endpoint, **args)

    return result


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


def non_match_for_deletion(str1: str, str2: str) -> bool:
    return str1 != str2 and str1.casefold() != str2.casefold()


def flash_non_match_for_deletion(str1: str, str2: str, message: str) -> bool:
    if non_match_for_deletion(str1, str2):
        flash(message, "danger")
        return False
    return True


def truncate(data: str, length: int) -> str:
    if not data:
        return data

    return (data[: length - 2] + "..") if len(data) > length else data


def get_share_links(url: str, title: str) -> dict:
    share_links = dict()
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(title)

    share_links["facebook"] = (
        f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    )
    share_links["twitter"] = (
        f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}"
    )
    share_links["email"] = f"mailto:?subject={encoded_title}&body={encoded_url}"
    share_links["whatsapp"] = f"whatsapp://send?text={encoded_url}"
    share_links["telegram"] = f"https://t.me/share/url?url={encoded_url}"
    share_links["url"] = url

    return share_links


def get_calendar_links_for_event_date(event_date) -> dict:
    calendar_links = dict()

    url = url_for("main.event_date", id=event_date.id, _external=True)
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(event_date.event.name)
    encoded_timezone = quote_plus(berlin_tz.key)

    start_date = event_date.start
    end_date = event_date.end if event_date.end else start_date
    date_format = "%Y%m%dT%H%M%S"

    if event_date.allday:
        date_format = "%Y%m%d"
        end_date = round_to_next_day(end_date)

    start = start_date.astimezone(berlin_tz).strftime(date_format)
    end = end_date.astimezone(berlin_tz).strftime(date_format)

    if (
        event_date.event.attendance_mode
        and event_date.event.attendance_mode != EventAttendanceMode.online
    ):
        location = get_place_str(event_date.event.event_place)
        locationParam = f"&location={quote_plus(location)}"
    else:
        locationParam = ""

    calendar_links["google"] = (
        f"http://www.google.com/calendar/event?action=TEMPLATE&text={encoded_title}&dates={start}/{end}&ctz={encoded_timezone}&details={encoded_url}{locationParam}"
    )

    calendar_links["ics"] = url_for(
        "main.event_date_ical", id=event_date.id, _external=True
    )

    return calendar_links


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


def get_calendar_links_for_event(event) -> dict:
    calendar_links = dict()
    calendar_links["ics"] = url_for("main.event_ical", id=event.id, _external=True)
    return calendar_links


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


def manage_required(permission=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(id, *args, **kwargs):
            admin_unit = get_admin_unit_for_manage_or_404(id)

            if permission and not has_access(
                admin_unit, permission
            ):  # pragma: no cover
                return permission_missing(
                    url_for("main.manage_admin_unit", id=admin_unit.id)
                )

            set_current_admin_unit(admin_unit)
            return f(id, *args, **kwargs)

        return decorated_function

    return decorator


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


def handle_base_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseError as e:
            flash(handleBaseError(e), "danger")

    return wrapper
