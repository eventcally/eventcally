from project.models import AdminUnit
from project.repos.base_repo import BaseRepo


class OrganizationRepo(BaseRepo[AdminUnit]):
    model_class = AdminUnit
