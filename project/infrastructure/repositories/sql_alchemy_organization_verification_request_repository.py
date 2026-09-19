from typing import Optional

from project.domain.events.organization_verification_requested import (
    OrganizationVerificationRequested,
)
from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)
from project.domain.repositories import (
    AbstractOrganizationVerificationRequestRepository,
)
from project.infrastructure.sql_error_translation import flush
from project.models.admin_unit_verification_request import AdminUnitVerificationRequest


class SqlAlchemyOrganizationVerificationRequestRepository(
    AbstractOrganizationVerificationRequestRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, verification_request: OrganizationVerificationRequestAggregate):
        model = AdminUnitVerificationRequest.from_aggregate(verification_request)
        self.session.add(model)
        flush(self.session)

        verification_request.id = model.id

        domain_event = verification_request.get_first_domain_event_by_type(
            OrganizationVerificationRequested
        )
        if domain_event:
            domain_event.id = model.id

    def _update(self, verification_request: OrganizationVerificationRequestAggregate):
        model = self._get_model(verification_request.id)
        model.fill_from_aggregate(verification_request)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[AdminUnitVerificationRequest]:
        return (
            self.session.query(AdminUnitVerificationRequest)
            .filter_by(id=object_id)
            .first()
        )

    def _get(
        self, object_id: int
    ) -> Optional[OrganizationVerificationRequestAggregate]:
        model = self._get_model(object_id)
        return AdminUnitVerificationRequest.to_aggregate(model) if model else None

    def _remove(self, verification_request: OrganizationVerificationRequestAggregate):
        model = self._get_model(verification_request.id)
        self.session.delete(model)
