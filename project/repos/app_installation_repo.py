from project.models import AppInstallation
from project.repos.base_repo import BaseRepo


class AppInstallationRepo(BaseRepo[AppInstallation]):
    model_class = AppInstallation
