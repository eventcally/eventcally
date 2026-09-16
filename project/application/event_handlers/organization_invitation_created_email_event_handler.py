from project.application.services.abstract_email_service import AbstractEmailService
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class OrganizationInvitationCreatedEmailEventHandler(AbstractEventHandler):
    def __init__(self, email_service: AbstractEmailService):
        super().__init__()
        self.email_service = email_service

    def handle(
        self, event: events.OrganizationInvitationCreated, uow: AbstractUnitOfWork
    ):
        admin_unit = uow.organizations.get(event.admin_unit_id)

        if not admin_unit:  # pragma: no cover
            return

        self.email_service.send_template_mail_to_address_async(
            event.email,
            "organization_invitation_notice",
            invitation_id=event.id,
            admin_unit_name=admin_unit.name,
        )
