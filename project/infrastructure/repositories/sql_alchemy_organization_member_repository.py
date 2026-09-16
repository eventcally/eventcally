from typing import Optional

from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.repositories.abstract_organization_member_repository import (
    AbstractOrganizationMemberRepository,
)
from project.infrastructure.sql_error_translation import flush
from project.models.admin_unit import AdminUnitMember
from project.models.user import User


class SqlAlchemyOrganizationMemberRepository(AbstractOrganizationMemberRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_all_with_permission(
        self, admin_unit_id: int, permission: str
    ) -> list[OrganisationMemberAggregate]:
        members: list[AdminUnitMember] = (
            AdminUnitMember.query.join(User)
            .filter(AdminUnitMember.admin_unit_id == admin_unit_id)
            .all()
        )
        models = list(filter(lambda member: member.has_permission(permission), members))
        return [AdminUnitMember.to_aggregate(m) for m in models]

    def _get_by_admin_unit_and_user(
        self, admin_unit_id: int, user_id: int
    ) -> Optional[OrganisationMemberAggregate]:
        model = self._get_model_by_admin_unit_and_user(admin_unit_id, user_id)
        return AdminUnitMember.to_aggregate(model) if model else None

    def _get_model_by_admin_unit_and_user(
        self, admin_unit_id: int, user_id: int
    ) -> Optional[AdminUnitMember]:
        return AdminUnitMember.query.filter_by(
            admin_unit_id=admin_unit_id, user_id=user_id
        ).first()

    def _add(self, member: OrganisationMemberAggregate):
        model = AdminUnitMember.from_aggregate(member)
        self.session.add(model)
        flush(self.session)

        member.id = model.id

    def _update(self, member: OrganisationMemberAggregate):
        model = self._get_model_by_admin_unit_and_user(
            member.admin_unit_id, member.user_id
        )
        model.fill_from_aggregate(member)
        self.session.merge(model)
        flush(self.session)
