from project.models import OAuth
from project.services.base_service import BaseService


class OAuthService(BaseService[OAuth]):
    model_class = OAuth
