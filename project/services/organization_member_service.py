from project.models import AdminUnitMember
from project.services.base_service import BaseService


class OrganizationMemberService(BaseService[AdminUnitMember]):
    model_class = AdminUnitMember
