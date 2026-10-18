from project.application import commands
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)
from project.application.services.abstract_email_service import AbstractEmailService
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .event_utils import ensure_event_exists


class ReportEventHandler(AbstractCommandHandler):
    def __init__(
        self,
        access_read_repo: AbstractAccessReadRepository,
        email_service: AbstractEmailService,
    ):
        super().__init__()
        self.access_read_repo = access_read_repo
        self.email_service = email_service

    def handle(self, cmd: commands.ReportEventCommand, uow: AbstractUnitOfWork):
        event = ensure_event_exists(cmd.event_id, uow)

        recipients = self.access_read_repo.event_report_recipients(
            event.admin_unit_id, "events:write"
        )

        self.email_service.send_template_mails_to_users_async(
            recipients,
            "event_report_notice",
            event=event,
            report={
                "contact_name": cmd.contact_name,
                "contact_email": cmd.contact_email,
                "message": cmd.message,
            },
        )
