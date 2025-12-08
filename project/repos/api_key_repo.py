from project.models import ApiKey
from project.repos.base_repo import BaseRepo


class ApiKeyRepo(BaseRepo[ApiKey]):
    model_class = ApiKey
