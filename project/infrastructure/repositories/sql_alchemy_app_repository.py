from project.domain.repositories.abstract_app_repository import AbstractAppRepository
from project.models import AppInstallation
from project.models.oauth import OAuth2Client


class SqlAlchemyAppRepository(AbstractAppRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, app: OAuth2Client):
        self.session.add(app)

    def _get(self, object_id: int) -> OAuth2Client:
        return (
            self.session.query(OAuth2Client)
            .filter(OAuth2Client.id == object_id)
            .filter(OAuth2Client.is_app)
            .first()
        )

    def _remove(self, app: OAuth2Client):
        self.session.delete(app)

    def _add_app_installation(self, app_installation: AppInstallation):
        self.session.add(app_installation)

    def _get_app_installation(self, object_id: int) -> AppInstallation:
        return (
            self.session.query(AppInstallation)
            .filter(AppInstallation.id == object_id)
            .first()
        )

    def _remove_app_installation(self, app_installation: AppInstallation):
        self.session.delete(app_installation)
