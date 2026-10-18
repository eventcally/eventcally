import importlib

from flask import current_app

from project.celery_init import celery, force_locale


def _load_class(class_path: str):
    """Resolves the `module.Class` path that the dispatchers write into messages."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# Task names are a wire contract with queued messages and the beat schedule;
# they keep their original module path even if this module moves.
@celery.task(
    name="project.base_tasks.send_mail_with_body_task",
    priority=0,
)
def send_mail_with_body_task(recipient, subject, body, html):
    mail_sender = current_app.container.infrastructure.mail_sender()

    with force_locale():
        mail_sender.send_mails_with_body([recipient], subject, body, html)


@celery.task(
    name="project.base_tasks.process_delayed_event",
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_delayed_event(event_class_path: str, event_dict: dict):
    event_class = _load_class(event_class_path)

    # Reconstruct the event using Pydantic's model_validate
    event = event_class.model_validate(event_dict)

    # Process through message bus
    message_bus = current_app.container.cqrs.message_bus()
    message_bus.handle(event)


@celery.task(
    name="project.base_tasks.process_delayed_event_v2",
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_delayed_event_v2(event_class_path: str, event_json: str):
    event_class = _load_class(event_class_path)

    event = event_class.model_validate_json(event_json)

    message_bus = current_app.container.cqrs.message_bus()
    message_bus.handle(event)


@celery.task(
    name="project.base_tasks.process_delayed_command",
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_delayed_command(command_class_path: str, command_dict: dict):
    command_class = _load_class(command_class_path)

    # Reconstruct the command using Pydantic's model_validate
    command = command_class.model_validate(command_dict)

    # Process through message bus
    message_bus = current_app.container.cqrs.message_bus()
    message_bus.handle(command)


@celery.task(
    name="project.base_tasks.process_delayed_command_v2",
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_delayed_command_v2(command_class_path: str, command_json: str):
    command_class = _load_class(command_class_path)

    command = command_class.model_validate_json(command_json)

    message_bus = current_app.container.cqrs.message_bus()
    message_bus.handle(command)
