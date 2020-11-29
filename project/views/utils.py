from project.models import Analytics
from project import db, mail
from flask_babelex import gettext
from flask import request, url_for, render_template, flash, redirect, Markup
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError


def track_analytics(key, value1, value2):
    result = Analytics(key=key, value1=value1)

    if value2 is not None:
        result.value2 = value2

    db.session.add(result)
    db.session.commit()

    return result


def handleSqlError(e: SQLAlchemyError) -> str:
    if e.orig:
        message = str(e.orig)
    else:
        message = str(e)
    print(message)
    return message


def get_pagination_urls(pagination, **kwargs):
    result = {}

    if pagination:
        if pagination.has_prev:
            args = request.args.copy()
            args.update(kwargs)
            args["page"] = pagination.prev_num
            result["prev_url"] = url_for(request.endpoint, **args)

        if pagination.has_next:
            args = request.args.copy()
            args.update(kwargs)
            args["page"] = pagination.next_num
            result["next_url"] = url_for(request.endpoint, **args)

    return result


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(
                gettext("Error in the %s field - %s")
                % (getattr(form, field).label.text, error),
                "danger",
            )


def flash_message(msg, url, link_text=None, category="success"):
    if not link_text:
        link_text = gettext("Show")
    link = ' &ndash; <a href="%s">%s</a>' % (url, link_text)
    message = Markup(msg + link)
    flash(message, category)


def permission_missing(redirect_location):
    flash("You do not have permission for this action", "danger")
    return redirect(redirect_location)


def send_mail(recipient, subject, template, **context):
    send_mails([recipient], subject, template, **context)


def send_mails(recipients, subject, template, **context):
    msg = Message(subject)
    msg.recipients = recipients
    msg.body = render_template("email/%s.txt" % template, **context)
    msg.html = render_template("email/%s.html" % template, **context)

    if not mail.default_sender:
        print(",".join(msg.recipients))
        print(msg.subject)
        print(msg.body)
        return

    mail.send(msg)
