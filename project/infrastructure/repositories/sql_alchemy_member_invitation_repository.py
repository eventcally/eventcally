from typing import Optional

from project.domain.events.member_invitation_created import MemberInvitationCreated
from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)
from project.domain.repositories import AbstractMemberInvitationRepository
from project.infrastructure.sql_error_translation import flush
from project.models.admin_unit import AdminUnitMemberInvitation


class SqlAlchemyMemberInvitationRepository(AbstractMemberInvitationRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, member_invitation: AdminUnitMemberInvitationAggregate):
        model = AdminUnitMemberInvitation.from_aggregate(member_invitation)
        self.session.add(model)
        flush(self.session)

        domain_event = member_invitation.get_first_domain_event_by_type(
            MemberInvitationCreated
        )
        member_invitation.id = model.id
        domain_event.id = model.id

    def _update(self, member_invitation: AdminUnitMemberInvitationAggregate):
        model = self._get_model(member_invitation.id)
        model.fill_from_aggregate(member_invitation)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[AdminUnitMemberInvitation]:
        return (
            self.session.query(AdminUnitMemberInvitation)
            .filter_by(id=object_id)
            .first()
        )

    def _get(self, object_id: int) -> Optional[AdminUnitMemberInvitationAggregate]:
        model = self._get_model(object_id)
        return AdminUnitMemberInvitation.to_aggregate(model) if model else None

    def _remove(self, member_invitation: AdminUnitMemberInvitationAggregate):
        model = self._get_model(member_invitation.id)
        self.session.delete(model)
