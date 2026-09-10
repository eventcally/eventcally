import abc
from typing import Optional, Set

from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)


class AbstractCustomWidgetRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[CustomWidgetAggregate] = set()

    def add(self, custom_widget: CustomWidgetAggregate):
        self._add(custom_widget)
        self.seen.add(custom_widget)

    def update(self, custom_widget: CustomWidgetAggregate):
        self._update(custom_widget)
        self.seen.add(custom_widget)

    def get(self, object_id: int) -> Optional[CustomWidgetAggregate]:
        custom_widget = self._get(object_id)
        if custom_widget:
            self.seen.add(custom_widget)
        return custom_widget

    def remove(self, custom_widget: CustomWidgetAggregate):
        self._remove(custom_widget)
        self.seen.add(custom_widget)

    @abc.abstractmethod
    def _add(self, custom_widget: CustomWidgetAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, custom_widget: CustomWidgetAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[CustomWidgetAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, custom_widget: CustomWidgetAggregate):  # pragma: no cover
        raise NotImplementedError
