import importlib

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


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_delayed_event(event_class_path: str, event_dict: dict):
    # Import the event class dynamically
    module_path, class_name = event_class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    event_class = getattr(module, class_name)

    # Reconstruct the event using Pydantic's model_validate
    event = event_class.model_validate(event_dict)

    # Process through message bus
    message_bus = app.container.cqrs.message_bus()
    message_bus.handle(event)
