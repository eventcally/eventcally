from project.models import OAuth2Client
from project.repos.base_repo import BaseRepo


class OAuth2ClientRepo(BaseRepo[OAuth2Client]):
    model_class = OAuth2Client
