from typing import Optional

from project.domain.events.app_created import AppCreated
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.repositories.abstract_app_repository import AbstractAppRepository
from project.models.oauth import OAuth2Client


class SqlAlchemyAppRepository(AbstractAppRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, app: AppAggregate):
        model = OAuth2Client.from_aggregate(app)
        self.session.add(model)
        self.session.flush()

        domain_event = app.get_first_domain_event_by_type(AppCreated)
        app.id = model.id
        domain_event.id = model.id

    def _update(self, app: AppAggregate):
        model = self._get_model(app.id)
        model.fill_from_aggregate(app)
        self.session.merge(model)
        self.session.flush()

    def _get_model(self, object_id: int) -> OAuth2Client:
        return (
            self.session.query(OAuth2Client)
            .filter(OAuth2Client.id == object_id)
            .filter(OAuth2Client.is_app)
            .first()
        )

    def _get(self, object_id: int) -> Optional[AppAggregate]:
        model = self._get_model(object_id)
        return OAuth2Client.to_aggregate(model)

    def _remove(self, app: AppAggregate):
        model = self._get_model(app.id)
        self.session.delete(model)
