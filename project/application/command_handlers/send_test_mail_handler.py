from project.application import commands
from project.application.services.abstract_email_service import AbstractEmailService
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import BaseError, MailDeliveryError

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin


class SendTestMailHandler(AbstractCommandHandler):
    def __init__(self, email_service: AbstractEmailService, site_name: str):
        super().__init__()
        self.email_service = email_service
        self.site_name = site_name

    def handle(self, cmd: commands.SendTestMailCommand, uow: AbstractUnitOfWork):
        ensure_actor_is_platform_admin(cmd.actor, uow)

        context = {"site_name": self.site_name}

        if cmd.asynchronous:
            job = self.email_service.send_template_mail_to_address_tracked(
                cmd.recipient, "test_email", **context
            )
            return commands.SendTestMailCommandResult(
                job_id=job.job_id, count=job.count
            )

        try:
            self.email_service.send_template_mail_to_address(
                cmd.recipient, "test_email", **context
            )
        except BaseError:
            raise
        except Exception as e:
            raise MailDeliveryError(str(e) or None, cause=e)

        return commands.SendTestMailCommandResult(count=1)
