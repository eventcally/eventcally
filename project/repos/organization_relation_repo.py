from project.models import AdminUnitRelation
from project.repos.base_repo import BaseRepo


class OrganizationRelationRepo(BaseRepo[AdminUnitRelation]):
    model_class = AdminUnitRelation
