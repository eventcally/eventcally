from project.models import AdminUnitMember
from project.repos.base_repo import BaseRepo


class OrganizationMemberRepo(BaseRepo[AdminUnitMember]):
    model_class = AdminUnitMember
