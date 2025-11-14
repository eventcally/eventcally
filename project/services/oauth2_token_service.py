from project.models import OAuth2Token
from project.services.base_service import BaseService


class OAuth2TokenService(BaseService[OAuth2Token]):
    model_class = OAuth2Token
