from project.application import commands
from project.application.read_repositories.abstract_user_admin_read_repository import (
    AbstractUserAdminReadRepository,
)
from project.application.services.abstract_email_service import AbstractEmailService
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin


class SendNewsletterHandler(AbstractCommandHandler):
    def __init__(
        self,
        email_service: AbstractEmailService,
        user_admin_read_repo: AbstractUserAdminReadRepository,
        site_name: str,
    ):
        super().__init__()
        self.email_service = email_service
        self.user_admin_read_repo = user_admin_read_repo
        self.site_name = site_name

    def handle(self, cmd: commands.SendNewsletterCommand, uow: AbstractUnitOfWork):
        ensure_actor_is_platform_admin(cmd.actor, uow)

        context = {"site_name": self.site_name, "message": cmd.message}

        if cmd.audience == "test":
            job = self.email_service.send_template_mail_to_address_tracked(
                cmd.test_recipient, "newsletter", **context
            )
        else:
            job = self.email_service.send_template_mails_to_users_tracked(
                self.user_admin_read_repo.list_newsletter_recipients(),
                "newsletter",
                **context,
            )

        return commands.SendNewsletterCommandResult(job_id=job.job_id, count=job.count)
