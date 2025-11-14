from project.models import AdminUnitMemberInvitation
from project.repos.base_repo import BaseRepo


class OrganizationMemberInvitationRepo(BaseRepo[AdminUnitMemberInvitation]):
    model_class = AdminUnitMemberInvitation
