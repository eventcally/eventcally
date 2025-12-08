from project.models import Settings
from project.services.base_service import BaseService


class SettingsService(BaseService[Settings]):
    model_class = Settings
