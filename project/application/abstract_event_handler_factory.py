import abc

from project.application.event_handlers.abstract_event_handler import (
    AbstractEventHandler,
)
from project.domain import events


class AbstractEventHandlerFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, event_type: type[events.Event]
    ) -> list[AbstractEventHandler]:  # pragma: no cover
        raise NotImplementedError
