from project.models import Role
from project.services.base_service import BaseService


class RoleService(BaseService[Role]):
    model_class = Role

    def upsert_role(self, role_name, role_title, permissions) -> Role:
        role = self.repo.get_role_by_name(role_name)

        if role is None:
            role = self.repo.create_role(role_name)

        role.title = role_title
        role.permissions = permissions
        self.repo.update_object(role)
        return role
