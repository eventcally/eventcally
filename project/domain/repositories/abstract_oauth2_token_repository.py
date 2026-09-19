import abc
from typing import Optional, Set

from project.domain.models.aggregates.oauth2_token_aggregate import OAuth2TokenAggregate


class AbstractOAuth2TokenRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OAuth2TokenAggregate] = set()

    def update(self, oauth2_token: OAuth2TokenAggregate):
        self._update(oauth2_token)
        self.seen.add(oauth2_token)

    def get(self, object_id: int) -> Optional[OAuth2TokenAggregate]:
        oauth2_token = self._get(object_id)
        if oauth2_token:
            self.seen.add(oauth2_token)
        return oauth2_token

    @abc.abstractmethod
    def _update(self, oauth2_token: OAuth2TokenAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[OAuth2TokenAggregate]:  # pragma: no cover
        raise NotImplementedError
