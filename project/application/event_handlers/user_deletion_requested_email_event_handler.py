from project.application.services.abstract_email_service import AbstractEmailService
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class UserDeletionRequestedEmailEventHandler(AbstractEventHandler):
    def __init__(self, email_service: AbstractEmailService):
        super().__init__()
        self.email_service = email_service

    def handle(self, event: events.UserDeletionRequested, uow: AbstractUnitOfWork):
        user = uow.users.get(event.id)

        if not user:  # pragma: no cover
            return

        self.email_service.send_template_mails_to_users_async(
            [user],
            "user_deletion_requested_notice",
            user=user,
        )
