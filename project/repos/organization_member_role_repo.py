from project.models import AdminUnitMemberRole
from project.repos.base_repo import BaseRepo


class OrganizationMemberRoleRepo(BaseRepo[AdminUnitMemberRole]):
    model_class = AdminUnitMemberRole

    def get_role_by_name(self, role_name) -> AdminUnitMemberRole | None:
        return AdminUnitMemberRole.query.filter_by(name=role_name).first()

    def create_role(self, role_name) -> AdminUnitMemberRole:
        role = AdminUnitMemberRole(name=role_name)
        self.insert_object(role)
        return role
