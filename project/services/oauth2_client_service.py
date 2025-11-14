from project.models import OAuth2Client
from project.services.base_service import BaseService


class OAuth2ClientService(BaseService[OAuth2Client]):
    model_class = OAuth2Client
