from functools import wraps
from itertools import groupby
from urllib.parse import quote_plus

from flask import current_app, flash, g, redirect, render_template, request, url_for
from flask_babel import force_locale, gettext
from flask_login.utils import decode_cookie
from flask_mail import Message
from flask_security import current_user
from markupsafe import Markup
from psycopg2.errorcodes import UNIQUE_VIOLATION
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.local import LocalProxy
from wtforms import FormField

from project import app, celery, mail
from project.access import (
    get_admin_unit_for_manage,
    get_admin_unit_for_manage_or_404,
    get_admin_unit_members_with_permission,
    get_admin_units_for_manage,
    has_access,
)
from project.dateutils import berlin_tz, round_to_next_day
from project.models import Event, EventAttendanceMode, EventDate
from project.utils import dummy_gettext, get_place_str, strings_are_equal_ignoring_case

mail_template_subject_mapping = {
    "event_report_notice": dummy_gettext("New event report"),
    "invitation_notice": dummy_gettext("You have received an invitation"),
    "newsletter": dummy_gettext("Newsletter from %(site_name)s"),
    "organization_deletion_requested_notice": dummy_gettext(
        "Organization deletion requested"
    ),
    "organization_invitation_accepted_notice": dummy_gettext(
        "Organization invitation accepted"
    ),
    "organization_invitation_notice": dummy_gettext("You have received an invitation"),
    "reference_auto_verified_notice": dummy_gettext(
        "New reference automatically verified"
    ),
    "reference_request_notice": dummy_gettext("New reference request"),
    "reference_request_review_status_notice": dummy_gettext(
        "Event review status updated"
    ),
    "referenced_event_changed_notice": dummy_gettext("Referenced event changed"),
    "review_notice": dummy_gettext("New event review"),
    "review_status_notice": dummy_gettext("Event review status updated"),
    "user_deletion_requested_notice": dummy_gettext("User deletion requested"),
    "test_email": dummy_gettext("Test mail from %(site_name)s"),
    "verification_request_notice": dummy_gettext("New verification request"),
    "verification_request_review_status_notice": dummy_gettext(
        "Verification request review status updated"
    ),
}


current_admin_unit = LocalProxy(lambda: get_current_admin_unit(False, False, False))


def set_current_admin_unit(admin_unit):
    if admin_unit:
        setattr(g, "manage_admin_unit", admin_unit)


def get_current_admin_unit(fallback=True, use_cookies=True, use_headers=False):
    admin_unit = getattr(g, "manage_admin_unit", None)

    if admin_unit:
        return admin_unit

    if current_user and current_user.is_authenticated:
        if use_cookies:
            admin_unit = get_current_admin_unit_from_cookies()

        if not admin_unit and use_headers:
            admin_unit = get_current_admin_unit_from_headers()

        if not admin_unit and fallback:
            admin_units = get_admin_units_for_manage()

            if len(admin_units) > 0:
                admin_unit = admin_units[0]

    if admin_unit:
        set_current_admin_unit(admin_unit)

    return admin_unit


def get_current_admin_unit_for_api():
    return get_current_admin_unit(fallback=False, use_cookies=False, use_headers=True)


def get_current_admin_unit_from_cookies():
    try:
        if request and request.cookies and "manage_admin_unit_id" in request.cookies:
            encoded = request.cookies.get("manage_admin_unit_id")
            manage_admin_unit_id = int(decode_cookie(encoded))
            return get_admin_unit_for_manage(manage_admin_unit_id)
    except Exception:
        pass

    return None


def get_current_admin_unit_from_headers():
    try:
        if request and request.headers and "X-OrganizationId" in request.headers:
            manage_admin_unit_id_str = request.headers["X-OrganizationId"]
            manage_admin_unit_id = int(manage_admin_unit_id_str)
            return get_admin_unit_for_manage(manage_admin_unit_id)
    except Exception:
        pass

    return None


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


def send_template_mail(recipient, template, **context):
    send_template_mails([recipient], template, **context)


def send_template_mails(recipients, template, **context):
    if len(recipients) == 0:  # pragma: no cover
        return

    subject, body, html = render_mail_body_with_subject(template, **context)
    send_mails_with_body(recipients, subject, body, html)


def send_template_mail_async(recipient, template, **context):
    return send_template_mails_async([recipient], template, **context)


def send_template_mails_async(recipients, template, **context):
    if len(recipients) == 0:  # pragma: no cover
        return

    subject, body, html = render_mail_body_with_subject(template, **context)
    return send_mails_with_body_async(recipients, subject, body, html)


def render_mail_body_with_subject(template, **context):
    subject_key = mail_template_subject_mapping.get(template)
    locale = context.get("locale", None) or app.config["BABEL_DEFAULT_LOCALE"]

    with force_locale(locale):
        subject = gettext(subject_key, **context)
        body, html = render_mail_body(template, **context)

    return subject, body, html


def send_template_mails_to_admin_unit_members_async(
    admin_unit_id, permissions, template, **context
):
    members = get_admin_unit_members_with_permission(admin_unit_id, permissions)
    users = [member.user for member in members]

    return send_template_mails_to_users_async(users, template, **context)


def send_template_mails_to_users_async(users, template, **context):
    if len(users) == 0:  # pragma: no cover
        return

    # Group by locale
    def locale_func(user):
        return user.locale if user.locale else ""

    sorted_users = sorted(users, key=locale_func)
    grouped_users = groupby(sorted_users, locale_func)

    signatures = list()

    for locale, locale_users in grouped_users:
        context["locale"] = locale
        subject, body, html = render_mail_body_with_subject(template, **context)
        signatures.extend([(user.email, subject, body, html) for user in locale_users])

    return send_mails_with_signatures_async(signatures)


def send_mails_with_body_async(recipients, subject, body, html):
    signatures = [(recipient, subject, body, html) for recipient in recipients]
    return send_mails_with_signatures_async(signatures)


def send_mails_with_signatures_async(signatures):
    from celery import group

    from project.base_tasks import send_mail_with_body_task

    if len(signatures) == 0:  # pragma: no cover
        return

    result = group(
        send_mail_with_body_task.s(*signature) for signature in signatures
    ).delay()
    return result


def render_mail_body(template, **context):
    body = render_template("email/%s.txt" % template, **context)
    html = render_template("email/%s.html" % template, **context)
    return body, html


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

    mail.send(msg)  # pragma: no cover


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


def get_calendar_links_for_event_date(event_date: EventDate) -> dict:
    calendar_links = dict()

    url = url_for("event_date", id=event_date.id, _external=True)
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(event_date.event.name)
    encoded_timezone = quote_plus(berlin_tz.zone)

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

    calendar_links["ics"] = url_for("event_date_ical", id=event_date.id, _external=True)

    return calendar_links


def get_calendar_links_for_event(event: Event) -> dict:
    calendar_links = dict()
    calendar_links["ics"] = url_for("event_ical", id=event.id, _external=True)
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


def get_celery_poll_result():  # pragma: no cover
    try:
        result = celery.AsyncResult(request.args["poll"])
        ready = result.ready()
        return {
            "ready": ready,
            "successful": result.successful() if ready else None,
            "value": result.get() if ready else result.result,
        }
    except Exception as e:
        return {
            "ready": True,
            "successful": False,
            "error": getattr(e, "message", "Unknown error"),
        }


def get_celery_poll_group_result():  # pragma: no cover
    try:
        result = celery.GroupResult.restore(request.args["poll"])
        ready = result.ready()
        return {
            "ready": ready,
            "count": len(result.children),
            "completed": result.completed_count(),
            "successful": result.successful() if ready else None,
        }
    except Exception as e:
        return {
            "ready": True,
            "successful": False,
            "error": getattr(e, "message", "Unknown error"),
        }


def manage_required(permission=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(id, *args, **kwargs):
            admin_unit = get_admin_unit_for_manage_or_404(id)

            if permission and not has_access(admin_unit, permission):
                return permission_missing(
                    url_for("manage_admin_unit", id=admin_unit.id)
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
                    url_for("manage_admin_unit", id=g.manage_admin_unit.id)
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_docs_url(path: str, **kwargs):  # pragma: no cover
    base_url = current_app.config["DOCS_URL"]
    if not base_url:
        return None

    return f"{base_url}{path}"
