from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class OrganizationInvitationAcceptedEmailEventHandler(AbstractEventHandler):
    def __init__(self, organization_service: OrganizationApplicationService):
        super().__init__()
        self.organization_service = organization_service

    def handle(
        self, event: events.OrganizationInvitationAccepted, uow: AbstractUnitOfWork
    ):
        self.organization_service.send_template_mails_to_members_async(
            uow,
            event.inviting_admin_unit_id,
            "organization_invitations:write",
            "organization_invitation_accepted_notice",
            email=event.accepting_user_email,
            new_admin_unit_name=event.new_admin_unit_name,
            inviting_admin_unit_id=event.inviting_admin_unit_id,
            relation_id=event.id,
        )
