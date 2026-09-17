import abc
from typing import Optional, Set

from project.domain.models.aggregates.settings_aggregate import SettingsAggregate


class AbstractSettingsRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[SettingsAggregate] = set()

    def add(self, settings: SettingsAggregate):
        self._add(settings)
        self.seen.add(settings)

    def update(self, settings: SettingsAggregate):
        self._update(settings)
        self.seen.add(settings)

    def get(self) -> Optional[SettingsAggregate]:
        settings = self._get()
        if settings:
            self.seen.add(settings)
        return settings

    @abc.abstractmethod
    def _add(self, settings: SettingsAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, settings: SettingsAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self) -> Optional[SettingsAggregate]:  # pragma: no cover
        raise NotImplementedError
