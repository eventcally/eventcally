from project.models import AdminUnitMemberRole
from project.services.base_service import BaseService


class OrganizationMemberRoleService(BaseService[AdminUnitMemberRole]):
    model_class = AdminUnitMemberRole

    def upsert_role(self, role_name, role_title, permissions) -> AdminUnitMemberRole:
        role = self.repo.get_role_by_name(role_name)

        if role is None:
            role = self.repo.create_role(role_name)

        role.title = role_title
        role.permissions = permissions
        self.repo.update_object(role)
        return role
