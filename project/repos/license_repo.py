from project.models import License
from project.repos.base_repo import BaseRepo


class LicenseRepo(BaseRepo[License]):
    model_class = License
