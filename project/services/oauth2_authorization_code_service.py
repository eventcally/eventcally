from project.models import OAuth2AuthorizationCode
from project.services.base_service import BaseService


class OAuth2AuthorizationCodeService(BaseService[OAuth2AuthorizationCode]):
    model_class = OAuth2AuthorizationCode
