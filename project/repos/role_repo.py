from project.models import Role
from project.repos.base_repo import BaseRepo


class RoleRepo(BaseRepo[Role]):
    model_class = Role

    def get_role_by_name(self, role_name) -> Role | None:
        return Role.query.filter_by(name=role_name).first()

    def create_role(self, role_name) -> Role:
        role = Role(name=role_name)
        self.insert_object(role)
        return role
