from project.models import AppKey
from project.repos.base_repo import BaseRepo


class AppKeyRepo(BaseRepo[AppKey]):
    model_class = AppKey
