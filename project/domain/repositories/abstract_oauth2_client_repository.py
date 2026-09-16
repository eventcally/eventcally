import abc
from typing import Optional, Set

from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)


class AbstractOAuth2ClientRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OAuth2ClientAggregate] = set()

    def add(self, oauth2_client: OAuth2ClientAggregate):
        self._add(oauth2_client)
        self.seen.add(oauth2_client)

    def update(self, oauth2_client: OAuth2ClientAggregate):
        self._update(oauth2_client)
        self.seen.add(oauth2_client)

    def get(self, object_id: int) -> Optional[OAuth2ClientAggregate]:
        oauth2_client = self._get(object_id)
        if oauth2_client:
            self.seen.add(oauth2_client)
        return oauth2_client

    def remove(self, oauth2_client: OAuth2ClientAggregate):
        self._remove(oauth2_client)
        self.seen.add(oauth2_client)

    @abc.abstractmethod
    def _add(self, oauth2_client: OAuth2ClientAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, oauth2_client: OAuth2ClientAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[OAuth2ClientAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, oauth2_client: OAuth2ClientAggregate):  # pragma: no cover
        raise NotImplementedError
