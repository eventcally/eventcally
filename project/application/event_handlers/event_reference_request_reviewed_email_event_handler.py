from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class EventReferenceRequestReviewedEmailEventHandler(AbstractEventHandler):
    def __init__(self, organization_service: OrganizationApplicationService):
        super().__init__()
        self.organization_service = organization_service

    def handle(
        self, event: events.EventReferenceRequestReviewed, uow: AbstractUnitOfWork
    ):
        referenced_event = uow.events.get(event.event_id)

        if not referenced_event:  # pragma: no cover
            return

        self.organization_service.send_template_mails_to_members_async(
            uow,
            referenced_event.admin_unit_id,
            "outgoing_event_reference_requests:write",
            "reference_request_review_status_notice",
            request=event,
            requester_admin_unit_id=referenced_event.admin_unit_id,
        )
