import importlib

from flask import current_app

from project.celery_init import celery, force_locale


@celery.task(
    priority=0,
)
def send_mail_with_body_task(recipient, subject, body, html):
    from project.views.utils import send_mails_with_body

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
    message_bus = current_app.container.cqrs.message_bus()
    message_bus.handle(event)


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_delayed_command(command_class_path: str, command_dict: dict):
    # Import the command class dynamically
    module_path, class_name = command_class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    command_class = getattr(module, class_name)

    # Reconstruct the command using Pydantic's model_validate
    command = command_class.model_validate(command_dict)

    # Process through message bus
    message_bus = current_app.container.cqrs.message_bus()
    message_bus.handle(command)
