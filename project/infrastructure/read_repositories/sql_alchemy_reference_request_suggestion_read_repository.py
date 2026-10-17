from typing import List

from sqlalchemy import select

from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_repositories.abstract_reference_request_suggestion_read_repository import (
    AbstractReferenceRequestSuggestionReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    AdminUnitRelation,
    Event,
    EventReference,
    EventReferenceRequest,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    to_organization_ref_read_model,
)


class SqlAlchemyReferenceRequestSuggestionReadRepository(
    AbstractReferenceRequestSuggestionReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _organizations(self, stmt) -> List[OrganizationRefReadModel]:
        return [
            to_organization_ref_read_model(admin_unit)
            for admin_unit in self.session.execute(stmt).scalars().all()
        ]

    def newest_requested_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:
        return self._organizations(
            select(AdminUnit)
            .join(
                EventReferenceRequest,
                EventReferenceRequest.admin_unit_id == AdminUnit.id,
            )
            .join(Event, EventReferenceRequest.event_id == Event.id)
            .where(
                Event.admin_unit_id == admin_unit_id,
                AdminUnit.id != admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
            .order_by(EventReferenceRequest.created_at.desc())
            .limit(limit)
        )

    def newest_referencing_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:
        return self._organizations(
            select(AdminUnit)
            .join(EventReference, EventReference.admin_unit_id == AdminUnit.id)
            .join(Event, EventReference.event_id == Event.id)
            .where(
                Event.admin_unit_id == admin_unit_id,
                AdminUnit.id != admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
            .order_by(EventReference.created_at.desc())
            .limit(limit)
        )

    def related_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:
        return self._organizations(
            select(AdminUnit)
            .join(
                AdminUnitRelation,
                AdminUnitRelation.source_admin_unit_id == AdminUnit.id,
            )
            .where(
                AdminUnitRelation.target_admin_unit_id == admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
            .order_by(
                AdminUnitRelation.auto_verify_event_reference_requests.desc(),
                AdminUnitRelation.verify.desc(),
                AdminUnitRelation.invited.desc(),
                AdminUnitRelation.created_at.desc(),
            )
            .limit(limit)
        )

    def other_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:
        return self._organizations(
            select(AdminUnit)
            .where(
                AdminUnit.id != admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
            .limit(limit)
        )
