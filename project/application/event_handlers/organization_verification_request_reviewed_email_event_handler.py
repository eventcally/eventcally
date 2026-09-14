from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class OrganizationVerificationRequestReviewedEmailEventHandler(AbstractEventHandler):
    def __init__(self, organization_service: OrganizationApplicationService):
        super().__init__()
        self.organization_service = organization_service

    def handle(
        self,
        event: events.OrganizationVerificationRequestReviewed,
        uow: AbstractUnitOfWork,
    ):
        self.organization_service.send_template_mails_to_members_async(
            uow,
            event.source_admin_unit_id,
            "outgoing_organization_verification_requests:write",
            "verification_request_review_status_notice",
            request=event,
        )
