from project.models import OAuth2AuthorizationCode
from project.repos.base_repo import BaseRepo


class OAuth2AuthorizationCodeRepo(BaseRepo[OAuth2AuthorizationCode]):
    model_class = OAuth2AuthorizationCode
