from project.models import ApiKey
from project.services.base_service import BaseService


class ApiKeyService(BaseService[ApiKey]):
    model_class = ApiKey
