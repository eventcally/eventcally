from project.models import OAuth2Client
from project.repos.base_repo import BaseRepo


class AppRepo(BaseRepo[OAuth2Client]):
    model_class = OAuth2Client

    def get_object_by_id(self, object_id) -> OAuth2Client:
        return (
            self.db.session.query(self.model_class)
            .filter(OAuth2Client.is_app)
            .filter(OAuth2Client.id == object_id)
            .first()
        )
