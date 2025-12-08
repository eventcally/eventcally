import datetime
from typing import Optional

from project.models import AdminUnit
from project.models.admin_unit import AdminUnitRelation
from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
)
from project.models.event_reference import EventReference
from project.models.event_reference_request import (
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from project.repos.event_repo import EventRepo
from project.repos.organization_relation_repo import OrganizationRelationRepo
from project.services import EventReferenceRequestService, EventReferenceService
from project.services.base_service import BaseService
from project.services.organization_verification_request_service import (
    OrganizationVerificationRequestService,
)
from project.views.utils import send_template_mails_to_admin_unit_members_async


class OrganizationService(BaseService[AdminUnit]):
    def __init__(
        self,
        repo,
        context_provider,
        event_reference_request_service: EventReferenceRequestService,
        organization_relation_repo: OrganizationRelationRepo,
        event_repo: EventRepo,
        event_reference_service: EventReferenceService,
        organization_verification_request_service: OrganizationVerificationRequestService,
        **kwargs
    ):
        super().__init__(repo, context_provider, **kwargs)
        self.event_reference_request_service = event_reference_request_service
        self.organization_relation_repo = organization_relation_repo
        self.event_repo = event_repo
        self.event_reference_service = event_reference_service
        self.organization_verification_request_service = (
            organization_verification_request_service
        )

    def verify_incoming_organization_verification_request(
        self,
        organization_verification_request: AdminUnitVerificationRequest,
        auto_verify_event_reference_requests: Optional[bool] = None,
    ) -> AdminUnitRelation:
        organization_verification_request.review_status = (
            AdminUnitVerificationRequestReviewStatus.verified
        )
        self.organization_verification_request_service.update_object(
            organization_verification_request
        )
        relation = self.update_organization_relation(
            organization_verification_request.target_admin_unit_id,
            organization_verification_request.source_admin_unit_id,
            verify=True,
            auto_verify_event_reference_requests=auto_verify_event_reference_requests,
        )
        return relation

    def update_organization_relation(
        self,
        source_organization_id,
        target_organization_id,
        verify: Optional[bool] = None,
        auto_verify_event_reference_requests: Optional[bool] = None,
    ) -> AdminUnitRelation:
        relation = self.organization_relation_repo.get_relation(
            source_organization_id, target_organization_id
        )

        if not relation:
            relation = self.organization_relation_repo.create_relation(
                source_organization_id, target_organization_id
            )

        if verify is not None:
            relation.verify = verify

        if auto_verify_event_reference_requests is not None:
            relation.auto_verify_event_reference_requests = (
                auto_verify_event_reference_requests
            )

        self.organization_relation_repo.update_object(relation)
        return relation

    def verify_incoming_event_reference_request(
        self, event_reference_request: EventReferenceRequest, rating: int = 50
    ) -> EventReference:
        event_reference_request.review_status = (
            EventReferenceRequestReviewStatus.verified
        )
        self.event_reference_request_service.update_object(event_reference_request)
        return self.event_reference_service.create_event_reference_for_request(
            event_reference_request, rating
        )

    def insert_outgoing_event_reference_request(
        self, event_reference_request: EventReferenceRequest
    ):
        event_id = event_reference_request.event_id or event_reference_request.event.id
        event = self.event_repo.get_object_by_id(event_id)

        source_admin_unit_id = (
            event_reference_request.admin_unit_id
            or event_reference_request.admin_unit.id
        )
        target_admin_unit_id = event.admin_unit_id
        relation = self.organization_relation_repo.get_relation(
            source_admin_unit_id,
            target_admin_unit_id,
        )
        auto_verify = relation and relation.auto_verify_event_reference_requests

        event_reference_request.review_status = (
            EventReferenceRequestReviewStatus.verified
            if auto_verify
            else EventReferenceRequestReviewStatus.inbox
        )

        self.event_reference_request_service.insert_object(event_reference_request)

        if auto_verify:
            event_reference = (
                self.event_reference_service.create_event_reference_for_request(
                    event_reference_request
                )
            )
            self._send_auto_reference_mails(event_reference)

    def _send_auto_reference_mails(self, reference: EventReference):
        send_template_mails_to_admin_unit_members_async(
            reference.admin_unit_id,
            "incoming_event_reference_requests:write",
            "reference_auto_verified_notice",
            reference=reference,
        )

    def request_deletion(self, object: AdminUnit):
        object.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        object.deletion_requested_by_id = self.context_provider.current_user_id_or_none
        self.repo.update_object(object)

        self._send_admin_unit_deletion_requested_mails(object)

    def _send_admin_unit_deletion_requested_mails(self, admin_unit: AdminUnit):
        from project.views.utils import send_template_mails_to_admin_unit_members_async

        send_template_mails_to_admin_unit_members_async(
            admin_unit.id,
            "settings:write",
            "organization_deletion_requested_notice",
            admin_unit=admin_unit,
        )
