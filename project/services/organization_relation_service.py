from project.models import AdminUnitRelation
from project.services.base_service import BaseService


class OrganizationRelationService(BaseService[AdminUnitRelation]):
    model_class = AdminUnitRelation
