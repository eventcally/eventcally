import uuid

from dependency_injector.wiring import Provide, inject
from flask import abort, current_app
from flask_babel import gettext
from flask_security import auth_required

from project.application.commands import SendNewsletterCommand, SendTestMailCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetMailJobStatusQuery,
    ListNewsletterRecipientsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.admin import bff_admin_bp
from project.presentation.bff.admin.schemas import (
    AdminMailConfig,
    AdminMailJob,
    AdminMailJobStatus,
    AdminNewsletterInfo,
    AdminNewsletterSend,
    AdminTestMailSend,
)
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.shared.query_results import result_or_404


def _current_actor():
    return current_app.container.context.context_provider().current_actor


@bff_route(
    bff_admin_bp,
    "/email",
    response=AdminMailConfig,
    summary="Get mail configuration",
)
@auth_required("session")
def get_mail_config():
    config = current_app.config
    port = config.get("MAIL_PORT")

    return AdminMailConfig(
        suppress_send=bool(config.get("MAIL_SUPPRESS_SEND")),
        server=config.get("MAIL_SERVER") or None,
        port=int(port) if port else None,
        use_tls=bool(config.get("MAIL_USE_TLS")),
        use_ssl=bool(config.get("MAIL_USE_SSL")),
        username=config.get("MAIL_USERNAME") or None,
        password_set=bool(config.get("MAIL_PASSWORD")),
        default_sender=_format_sender(config.get("MAIL_DEFAULT_SENDER")),
    )


def _format_sender(sender):
    if not sender:
        return None
    if isinstance(sender, (tuple, list)):
        return " ".join(str(part) for part in sender if part)
    return str(sender)


@bff_route(
    bff_admin_bp,
    "/email/test",
    method="POST",
    body=AdminTestMailSend,
    response=AdminMailJob,
    summary="Send test mail",
)
@auth_required("session")
@inject
def send_test_mail(
    body: AdminTestMailSend,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    result = message_bus.handle_command(
        SendTestMailCommand(
            actor=_current_actor(),
            recipient=str(body.recipient),
            asynchronous=body.asynchronous,
        )
    )
    return AdminMailJob(job_id=result.job_id, count=result.count)


@bff_route(
    bff_admin_bp,
    "/newsletter",
    response=AdminNewsletterInfo,
    summary="Get newsletter info",
)
@auth_required("session")
@inject
def get_newsletter_info(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    recipients = query_bus.handle(ListNewsletterRecipientsQuery())
    return AdminNewsletterInfo(recipient_count=len(recipients))


@bff_route(
    bff_admin_bp,
    "/newsletter",
    method="POST",
    body=AdminNewsletterSend,
    response=AdminMailJob,
    summary="Send newsletter",
)
@auth_required("session")
@inject
def send_newsletter(
    body: AdminNewsletterSend,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    # A missing recipient must never mean "everyone"; the command validates it again.
    if body.audience == "test" and not body.test_recipient:
        raise FieldValidationError(
            ["test_recipient"], gettext("This field is required.")
        )
    if body.audience == "all" and body.test_recipient:
        raise FieldValidationError(["audience"], gettext("Not a valid choice"))

    result = message_bus.handle_command(
        SendNewsletterCommand(
            actor=_current_actor(),
            audience=body.audience,
            test_recipient=str(body.test_recipient) if body.test_recipient else None,
            message=body.message,
        )
    )
    return AdminMailJob(job_id=result.job_id, count=result.count)


@bff_route(
    bff_admin_bp,
    "/mail-jobs/<job_id>",
    response=AdminMailJobStatus,
    summary="Get mail job status",
)
@auth_required("session")
@inject
def get_mail_job_status(
    job_id: str, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    try:
        uuid.UUID(job_id)
    except ValueError:
        abort(404)

    status = result_or_404(query_bus.handle(GetMailJobStatusQuery(job_id=job_id)))
    return AdminMailJobStatus(**status.model_dump())
