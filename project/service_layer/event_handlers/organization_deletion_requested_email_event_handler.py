from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.services.organization_service import OrganizationService

from .abstract_event_handler import AbstractEventHandler


class OrganizationDeletionRequestedEmailEventHandler(AbstractEventHandler):
    def __init__(self, organization_service: OrganizationService):
        super().__init__()
        self.organization_service = organization_service

    def handle(
        self, event: events.OrganizationDeletionRequested, uow: AbstractUnitOfWork
    ):
        with uow:
            organization = uow.organizations.get(event.id)

            if not organization:  # pragma: no cover
                return

            self.organization_service.send_template_mails_to_members_async(
                uow,
                organization.id,
                "settings:write",
                "organization_deletion_requested_notice",
                admin_unit=organization,
            )
