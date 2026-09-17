from typing import Optional

from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.repositories import AbstractOrganizationRepository
from project.infrastructure.sql_error_translation import flush
from project.models import AdminUnit


class SqlAlchemyOrganizationRepository(AbstractOrganizationRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, organization: OrganizationAggregate):
        model = AdminUnit.from_aggregate(organization)
        self.session.add(model)
        flush(self.session)

        organization.id = model.id

    def _update(self, organization: OrganizationAggregate):
        model = self._get_model(organization.id)
        model.fill_from_aggregate(organization)
        self.session.merge(model)
        self.session.flush()

    def _get_model(self, object_id: int) -> AdminUnit:
        return self.session.query(AdminUnit).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[OrganizationAggregate]:
        model = self._get_model(object_id)
        return AdminUnit.to_aggregate(model) if model else None
