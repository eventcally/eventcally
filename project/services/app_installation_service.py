from project.models import AppInstallation
from project.services.base_service import BaseService


class AppInstallationService(BaseService[AppInstallation]):
    model_class = AppInstallation
