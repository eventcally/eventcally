import abc
from typing import Optional, Set

from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.domain.types import ObjectId


class AbstractApiKeyRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[ApiKeyAggregate] = set()

    def add(self, api_key: ApiKeyAggregate):
        self._add(api_key)
        self.seen.add(api_key)

    def update(self, api_key: ApiKeyAggregate):
        self._update(api_key)
        self.seen.add(api_key)

    def get(self, object_id: int) -> Optional[ApiKeyAggregate]:
        api_key = self._get(object_id)
        if api_key:
            self.seen.add(api_key)
        return api_key

    def remove(self, api_key: ApiKeyAggregate):
        self._remove(api_key)
        self.seen.add(api_key)

    def count_for_owner(
        self, user_id: Optional[ObjectId], admin_unit_id: Optional[ObjectId]
    ) -> int:
        return self._count_for_owner(user_id, admin_unit_id)

    @abc.abstractmethod
    def _add(self, api_key: ApiKeyAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, api_key: ApiKeyAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> Optional[ApiKeyAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, api_key: ApiKeyAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _count_for_owner(
        self, user_id: Optional[ObjectId], admin_unit_id: Optional[ObjectId]
    ) -> int:  # pragma: no cover
        raise NotImplementedError
