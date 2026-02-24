from project.domain.repositories import AbstractOrganizationRepository
from project.domain.types.object_id import ObjectId
from project.models import AdminUnit
from project.models.admin_unit import AdminUnitMember
from project.models.user import User


class SqlAlchemyOrganizationRepository(AbstractOrganizationRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, organization: AdminUnit):  # pragma: no cover
        self.session.add(organization)

    def _get(self, object_id: int) -> AdminUnit:
        return self.session.query(AdminUnit).filter_by(id=object_id).first()

    def _remove(self, organization: AdminUnit):  # pragma: no cover
        self.session.delete(organization)

    def _get_members_with_permission(
        self, organization_id: ObjectId, permission: str
    ) -> list[AdminUnitMember]:
        members: list[AdminUnitMember] = (
            AdminUnitMember.query.join(User)
            .filter(AdminUnitMember.admin_unit_id == organization_id)
            .all()
        )

        return list(filter(lambda member: member.has_permission(permission), members))
