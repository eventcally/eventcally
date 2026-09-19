import abc
from typing import Optional, Set

from project.domain.models.aggregates.app_key_aggregate import AppKeyAggregate
from project.domain.types.object_id import ObjectId


class AbstractAppKeyRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[AppKeyAggregate] = set()

    def add(self, app_key: AppKeyAggregate):
        self._add(app_key)
        self.seen.add(app_key)

    def get(self, object_id: ObjectId) -> Optional[AppKeyAggregate]:
        app_key = self._get(object_id)
        if app_key:
            self.seen.add(app_key)
        return app_key

    def remove(self, app_key: AppKeyAggregate):
        self._remove(app_key)
        self.seen.add(app_key)

    @abc.abstractmethod
    def _add(self, app_key: AppKeyAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: ObjectId
    ) -> Optional[AppKeyAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, app_key: AppKeyAggregate):  # pragma: no cover
        raise NotImplementedError
