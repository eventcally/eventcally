from typing import Optional

from project.domain.events.organization_invitation_created import (
    OrganizationInvitationCreated,
)
from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)
from project.domain.repositories import AbstractOrganizationInvitationRepository
from project.infrastructure.sql_error_translation import flush
from project.models.admin_unit import AdminUnitInvitation


class SqlAlchemyOrganizationInvitationRepository(
    AbstractOrganizationInvitationRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, organization_invitation: AdminUnitInvitationAggregate):
        model = AdminUnitInvitation.from_aggregate(organization_invitation)
        self.session.add(model)
        flush(self.session)

        domain_event = organization_invitation.get_first_domain_event_by_type(
            OrganizationInvitationCreated
        )
        organization_invitation.id = model.id
        domain_event.id = model.id

    def _update(self, organization_invitation: AdminUnitInvitationAggregate):
        model = self._get_model(organization_invitation.id)
        model.fill_from_aggregate(organization_invitation)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[AdminUnitInvitation]:
        return self.session.query(AdminUnitInvitation).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[AdminUnitInvitationAggregate]:
        model = self._get_model(object_id)
        return AdminUnitInvitation.to_aggregate(model) if model else None

    def _remove(self, organization_invitation: AdminUnitInvitationAggregate):
        model = self._get_model(organization_invitation.id)
        self.session.delete(model)
