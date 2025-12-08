from project.models import OAuth2Token
from project.repos.base_repo import BaseRepo


class OAuth2TokenRepo(BaseRepo[OAuth2Token]):
    model_class = OAuth2Token
