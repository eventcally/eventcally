from project.models import License
from project.services.base_service import BaseService


class LicenseService(BaseService[License]):
    model_class = License
