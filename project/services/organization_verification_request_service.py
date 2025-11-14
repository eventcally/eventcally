from project.models import AdminUnitVerificationRequest
from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequestReviewStatus,
)
from project.services.base_service import BaseService
from project.views.utils import send_template_mails_to_admin_unit_members_async


class OrganizationVerificationRequestService(BaseService[AdminUnitVerificationRequest]):

    def insert_object(self, object: AdminUnitVerificationRequest):
        super().insert_object(object)

        if object.review_status == AdminUnitVerificationRequestReviewStatus.inbox:
            self._send_verification_request_inbox_mails(object)

    def update_object(self, object: AdminUnitVerificationRequest):
        super().update_object(object)

        self._send_verification_request_review_status_mails(object)

    def _send_verification_request_inbox_mails(
        self, request: AdminUnitVerificationRequest
    ):
        # Benachrichtige alle Mitglieder der AdminUnit, die Requests verifizieren können
        admin_unit_id = request.target_admin_unit_id or request.target_admin_unit.id
        send_template_mails_to_admin_unit_members_async(
            admin_unit_id,
            "incoming_organization_verification_requests:write",
            "verification_request_notice",
            request=request,
        )

    def _send_verification_request_review_status_mails(
        self, request: AdminUnitVerificationRequest
    ):
        # Benachrichtige alle Mitglieder der AdminUnit, die diesen Request erstellt hatte
        send_template_mails_to_admin_unit_members_async(
            request.source_admin_unit_id,
            "outgoing_organization_verification_requests:write",
            "verification_request_review_status_notice",
            request=request,
        )
