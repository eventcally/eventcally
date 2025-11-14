from project.models import OAuth2Client
from project.repos.app_key_repo import AppKeyRepo
from project.services.base_service import BaseService


class AppService(BaseService[OAuth2Client]):
    model_class = OAuth2Client

    def __init__(self, repo, context_provider, app_key_repo: AppKeyRepo, **kwargs):
        super().__init__(repo, context_provider, **kwargs)
        self.app_key_repo = app_key_repo

    def get_app_key_by_id(self, app: OAuth2Client, app_key_id):
        app_key = self.app_key_repo.get_object_by_id(app_key_id)
        return app_key if app_key and app_key.oauth2_client_id == app.id else None

    def insert_app_key(self, app: OAuth2Client, app_key):
        app_key.oauth2_client_id = app.id
        self.app_key_repo.insert_object(app_key)

    def delete_app_key(self, app: OAuth2Client, app_key):
        self.app_key_repo.delete_object(app_key)
