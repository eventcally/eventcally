from project import app, celery
from project.celery_init import force_locale
from project.views.utils import send_mails_with_body


@celery.task(
    base=getattr(app, "celery_http_task_cls"),
    priority=0,
)
def send_mail_with_body_task(recipient, subject, body, html):
    with force_locale():
        send_mails_with_body([recipient], subject, body, html)
