import abc
from typing import Set

from project.domain.models.aggregates.app_aggregate import AppAggregate


class AbstractAppRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[AppAggregate] = set()

    def add(self, app: AppAggregate):
        self._add(app)
        self.seen.add(app)

    def update(self, app: AppAggregate):
        self._update(app)
        self.seen.add(app)

    def get(self, object_id: int) -> AppAggregate:
        app = self._get(object_id)
        if app:
            self.seen.add(app)
        return app

    def remove(self, app: AppAggregate):
        self._remove(app)
        self.seen.add(app)

    @abc.abstractmethod
    def _add(self, app: AppAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, app: AppAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> AppAggregate:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, app: AppAggregate):  # pragma: no cover
        raise NotImplementedError
