from models import Image, Analytics
from app import db, mail
from flask_babelex import gettext
from flask import request, url_for, render_template, flash
from flask_mail import Message

def track_analytics(key, value1, value2):
    result = Analytics(key = key, value1 = value1)

    if value2 is not None:
        result.value2 = value2

    db.session.add(result)
    db.session.commit()

    return result

def handleSqlError(e):
    message = str(e.__dict__['orig'])
    print(message)
    return message

def upsert_image_with_data(image, data, encoding_format = "image/jpeg"):
    if image is None:
        image = Image()

    image.data = data
    image.encoding_format = encoding_format

    return image

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
            flash(gettext("Error in the %s field - %s") % (
                getattr(form, field).label.text,
                error
            ), 'danger')

def permission_missing(redirect_location):
    flash('You do not have permission for this action', 'danger')
    return redirect(redirect_location)

def send_mail(recipient, subject, template, **context):
    send_mails([recipient], subject, template, **context)

def send_mails(recipients, subject, template, **context):
    msg = Message(subject)
    msg.recipients = recipients
    msg.body = render_template("email/%s.txt" % template, **context)
    msg.html = render_template("email/%s.html" % template, **context)
    mail.send(msg)