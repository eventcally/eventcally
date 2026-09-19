from typing import Optional

from project.domain.events.organization_invitation_accepted import (
    OrganizationInvitationAccepted,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.repositories import AbstractOrganizationRelationRepository
from project.infrastructure.sql_error_translation import flush
from project.models.admin_unit import AdminUnitRelation


class SqlAlchemyOrganizationRelationRepository(AbstractOrganizationRelationRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, organization_relation: OrganizationRelationAggregate):
        model = AdminUnitRelation.from_aggregate(organization_relation)
        self.session.add(model)
        flush(self.session)

        organization_relation.id = model.id

        domain_event = organization_relation.get_first_domain_event_by_type(
            OrganizationInvitationAccepted
        )
        if domain_event:
            domain_event.id = model.id

    def _update(self, organization_relation: OrganizationRelationAggregate):
        model = self._get_model(organization_relation.id)
        model.fill_from_aggregate(organization_relation)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[AdminUnitRelation]:
        return self.session.query(AdminUnitRelation).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[OrganizationRelationAggregate]:
        model = self._get_model(object_id)
        return AdminUnitRelation.to_aggregate(model) if model else None

    def _get_by_source_and_target(
        self, source_admin_unit_id: int, target_admin_unit_id: int
    ) -> Optional[OrganizationRelationAggregate]:
        model = (
            self.session.query(AdminUnitRelation)
            .filter_by(
                source_admin_unit_id=source_admin_unit_id,
                target_admin_unit_id=target_admin_unit_id,
            )
            .first()
        )
        return AdminUnitRelation.to_aggregate(model) if model else None

    def _remove(self, organization_relation: OrganizationRelationAggregate):
        model = self._get_model(organization_relation.id)
        self.session.delete(model)
