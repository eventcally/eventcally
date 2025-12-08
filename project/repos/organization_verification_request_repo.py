from project.models import AdminUnitVerificationRequest
from project.repos.base_repo import BaseRepo


class OrganizationVerificationRequestRepo(BaseRepo[AdminUnitVerificationRequest]):
    model_class = AdminUnitVerificationRequest
