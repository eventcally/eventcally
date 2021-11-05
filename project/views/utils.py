from urllib.parse import quote_plus

from flask import Markup, flash, g, redirect, render_template, request, url_for
from flask_babelex import gettext
from flask_login.utils import decode_cookie
from flask_mail import Message
from flask_security import current_user
from psycopg2.errorcodes import UNIQUE_VIOLATION
from sqlalchemy.exc import SQLAlchemyError
from wtforms import FormField

from project import app, db, mail
from project.access import get_admin_unit_for_manage, get_admin_units_for_manage
from project.dateutils import berlin_tz, round_to_next_day
from project.models import Analytics, EventAttendanceMode, EventDate
from project.utils import get_place_str, strings_are_equal_ignoring_case


def set_current_admin_unit(admin_unit):
    if admin_unit:
        setattr(g, "manage_admin_unit", admin_unit)


def get_current_admin_unit(fallback=True):
    admin_unit = getattr(g, "manage_admin_unit", None)

    if admin_unit:
        return admin_unit

    if current_user.is_authenticated:
        admin_unit = get_current_admin_unit_from_cookies()

        if not admin_unit and fallback:
            admin_units = get_admin_units_for_manage()

            if len(admin_units) > 0:
                admin_unit = admin_units[0]

    if admin_unit:
        set_current_admin_unit(admin_unit)

    return admin_unit


def get_current_admin_unit_from_cookies():
    try:
        if "manage_admin_unit_id" in request.cookies:
            encoded = request.cookies.get("manage_admin_unit_id")
            manage_admin_unit_id = int(decode_cookie(encoded))
            return get_admin_unit_for_manage(manage_admin_unit_id)
    except Exception:
        pass

    return None


def track_analytics(key, value1, value2):
    result = Analytics(key=key, value1=value1)

    if value2 is not None:
        result.value2 = value2

    db.session.add(result)
    db.session.commit()

    return result


def handleSqlError(e: SQLAlchemyError) -> str:
    if not e.orig:
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

        if isinstance(field, FormField):
            flash_errors(field.form, field_label)
            continue

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


def send_mail(recipient, subject, template, **context):
    send_mails([recipient], subject, template, **context)


def send_mails(recipients, subject, template, **context):
    if len(recipients) == 0:  # pragma: no cover
        return

    body = render_template("email/%s.txt" % template, **context)
    html = render_template("email/%s.html" % template, **context)
    send_mails_with_body(recipients, subject, body, html)


def send_mails_with_body(recipients, subject, body, html):
    # Send single mails, otherwise recipients will see each other
    for recipient in recipients:
        msg = Message(subject)
        msg.recipients = [recipient]
        msg.body = body
        msg.html = html
        send_mail_message(msg)


def send_mail_message(msg):
    if not mail.default_sender:
        app.logger.info(",".join(msg.recipients))
        app.logger.info(msg.subject)
        app.logger.info(msg.body)
        return

    mail.send(msg)


def non_match_for_deletion(str1: str, str2: str) -> bool:
    return str1 != str2 and str1.casefold() != str2.casefold()


def truncate(data: str, length: int) -> str:
    if not data:
        return data

    return (data[: length - 2] + "..") if len(data) > length else data


def get_share_links(url: str, title: str) -> dict:
    share_links = dict()
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(title)

    share_links[
        "facebook"
    ] = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    share_links[
        "twitter"
    ] = f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}"
    share_links["email"] = f"mailto:?subject={encoded_title}&body={encoded_url}"
    share_links["whatsapp"] = f"whatsapp://send?text={encoded_url}"
    share_links["telegram"] = f"https://t.me/share/url?url={encoded_url}"
    share_links["url"] = url

    return share_links


def get_calendar_links(event_date: EventDate) -> dict:
    calendar_links = dict()

    url = url_for("event_date", id=event_date.id, _external=True)
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(event_date.event.name)
    encoded_timezone = quote_plus(berlin_tz.zone)

    start_date = event_date.start
    end_date = event_date.end if event_date.end else start_date
    date_format = "%Y%m%dT%H%M%S"

    if event_date.event.allday:
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

    calendar_links[
        "google"
    ] = f"http://www.google.com/calendar/event?action=TEMPLATE&text={encoded_title}&dates={start}/{end}&ctz={encoded_timezone}&details={encoded_url}{locationParam}"

    calendar_links["ics"] = url_for("event_date_ical", id=event_date.id, _external=True)

    return calendar_links


def get_invitation_access_result(email: str):
    from project.services.user import find_user_by_email

    # Wenn der aktuelle Nutzer nicht der Empfänger der Einladung ist, Meldung ausgeben
    if current_user.is_authenticated and not strings_are_equal_ignoring_case(
        email, current_user.email
    ):
        return permission_missing(
            url_for("profile"),
            gettext(
                "The invitation was issued to another user. Sign in with the email address the invitation was sent to."
            ),
        )

    # Wenn Email nicht als Nutzer vorhanden, dann direkt zu Registrierung
    if not find_user_by_email(email):
        return redirect(url_for("security.register"))

    # Wenn nicht angemeldet, dann zum Login
    if not current_user.is_authenticated:
        return app.login_manager.unauthorized()

    return None
