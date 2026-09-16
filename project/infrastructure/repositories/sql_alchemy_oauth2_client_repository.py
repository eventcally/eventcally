from typing import Optional

from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)
from project.domain.repositories import AbstractOAuth2ClientRepository
from project.infrastructure.sql_error_translation import flush
from project.models.oauth import OAuth2Client


class SqlAlchemyOAuth2ClientRepository(AbstractOAuth2ClientRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, oauth2_client: OAuth2ClientAggregate):
        model = OAuth2Client.from_oauth2_client_aggregate(oauth2_client)
        self.session.add(model)
        flush(self.session)

        oauth2_client.id = model.id

    def _update(self, oauth2_client: OAuth2ClientAggregate):
        model = self._get_model(oauth2_client.id)
        model.fill_from_oauth2_client_aggregate(oauth2_client)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[OAuth2Client]:
        return (
            self.session.query(OAuth2Client)
            .filter(OAuth2Client.id == object_id)
            .filter(OAuth2Client.is_app.is_(False))
            .first()
        )

    def _get(self, object_id: int) -> Optional[OAuth2ClientAggregate]:
        model = self._get_model(object_id)
        return OAuth2Client.to_oauth2_client_aggregate(model) if model else None

    def _remove(self, oauth2_client: OAuth2ClientAggregate):
        model = self._get_model(oauth2_client.id)
        self.session.delete(model)
