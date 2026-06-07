import abc

from project.domain import events


class AbstractEventDispatcher(abc.ABC):
    @abc.abstractmethod
    def dispatch(self, event: events.Event):  # pragma: no cover
        raise NotImplementedError
