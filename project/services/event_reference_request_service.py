from project.models import EventReferenceRequest
from project.models.event_reference_request import EventReferenceRequestReviewStatus
from project.services.base_service import BaseService
from project.views.utils import send_template_mails_to_admin_unit_members_async


class EventReferenceRequestService(BaseService[EventReferenceRequest]):

    def insert_object(self, object: EventReferenceRequest):
        super().insert_object(object)

        if object.review_status == EventReferenceRequestReviewStatus.inbox:
            self._send_reference_request_inbox_mails(object)

    def update_object(self, object: EventReferenceRequest):
        super().update_object(object)

        self._send_reference_request_review_status_mails(object)

    def _send_reference_request_inbox_mails(self, request: EventReferenceRequest):
        send_template_mails_to_admin_unit_members_async(
            request.admin_unit_id,
            "incoming_event_reference_requests:write",
            "reference_request_notice",
            request=request,
        )

    def _send_reference_request_review_status_mails(
        self, request: EventReferenceRequest
    ):
        # Benachrichtige alle Mitglieder der AdminUnit, die diesen Request erstellt hatte
        send_template_mails_to_admin_unit_members_async(
            request.event.admin_unit_id,
            "outgoing_event_reference_requests:write",
            "reference_request_review_status_notice",
            request=request,
        )
