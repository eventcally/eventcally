from project.models import Settings
from project.repos.base_repo import BaseRepo


class SettingsRepo(BaseRepo[Settings]):
    model_class = Settings
