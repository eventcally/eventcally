from project.models import OAuth
from project.repos.base_repo import BaseRepo


class OAuthRepo(BaseRepo[OAuth]):
    model_class = OAuth
