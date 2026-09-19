from project.application.read_repositories.abstract_event_read_repository import (
    AbstractEventReadRepository,
)
from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class EventReferenceRequestCreatedEmailEventHandler(AbstractEventHandler):
    def __init__(
        self,
        organization_service: OrganizationApplicationService,
        event_read_repo: AbstractEventReadRepository,
    ):
        super().__init__()
        self.organization_service = organization_service
        self.event_read_repo = event_read_repo

    def handle(
        self, event: events.EventReferenceRequestCreated, uow: AbstractUnitOfWork
    ):
        event_read_model = self.event_read_repo.get(event.event_id)

        self.organization_service.send_template_mails_to_members_async(
            uow,
            event.admin_unit_id,
            "incoming_event_reference_requests:write",
            "reference_request_notice",
            request=event,
            event=event_read_model,
        )
