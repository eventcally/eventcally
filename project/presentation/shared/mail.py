from itertools import groupby

from flask import current_app, render_template
from flask_babel import force_locale, gettext
from flask_mail import Message

from project.application.queries import ListEventReportRecipientsQuery
from project.extensions import mail
from project.shared.utils import dummy_gettext

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
    locale = context.get("locale", None) or current_app.config["BABEL_DEFAULT_LOCALE"]

    with force_locale(locale):
        subject = gettext(subject_key, **context)
        body, html = render_mail_body(template, **context)

    return subject, body, html


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
        current_app.logger.info(",".join(msg.recipients))
        current_app.logger.info(msg.subject)
        current_app.logger.info(msg.body)
        return

    mail.send(msg)  # pragma: no cover


def send_event_report_mails(event, report: dict):
    # Members of the organization who may edit events, plus platform admins
    users = current_app.container.cqrs.query_bus().handle(
        ListEventReportRecipientsQuery(admin_unit_id=event.admin_unit_id)
    )

    send_template_mails_to_users_async(
        users,
        "event_report_notice",
        event=event,
        report=report,
    )
