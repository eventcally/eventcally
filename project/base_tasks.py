from project import app, celery
from project.views.utils import send_mail


@celery.task(
    base=getattr(app, "celery_http_task_cls"),
    priority=0,
)
def send_mail_task(recipient, subject, template):
    send_mail(recipient, subject, template)
