import time
from typing import Optional

from project.domain.models.aggregates.oauth2_token_aggregate import OAuth2TokenAggregate
from project.domain.repositories.abstract_oauth2_token_repository import (
    AbstractOAuth2TokenRepository,
)
from project.infrastructure.sql_error_translation import flush
from project.models.oauth import OAuth2Token


class SqlAlchemyOAuth2TokenRepository(AbstractOAuth2TokenRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_model(self, object_id: int) -> Optional[OAuth2Token]:
        return self.session.query(OAuth2Token).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[OAuth2TokenAggregate]:
        model = self._get_model(object_id)
        if model is None:
            return None

        return OAuth2TokenAggregate(
            id=model.id,
            user_id=model.user_id,
            is_revoked=model.access_token_revoked_at > 0,
        )

    def _update(self, oauth2_token: OAuth2TokenAggregate):
        model = self._get_model(oauth2_token.id)
        if oauth2_token.is_revoked:
            model.access_token_revoked_at = int(time.time())
        self.session.merge(model)
        flush(self.session)
