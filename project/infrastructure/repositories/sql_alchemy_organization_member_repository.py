from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.repositories.abstract_organization_member_repository import (
    AbstractOrganizationMemberRepository,
)
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
