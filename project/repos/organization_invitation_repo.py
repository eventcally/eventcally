from project.models import AdminUnitInvitation
from project.repos.base_repo import BaseRepo


class OrganizationInvitationRepo(BaseRepo[AdminUnitInvitation]):
    model_class = AdminUnitInvitation
