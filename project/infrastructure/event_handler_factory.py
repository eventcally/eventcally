from dependency_injector.errors import NoSuchProviderError

from project.application.abstract_event_handler_factory import (
    AbstractEventHandlerFactory,
)
from project.application.event_handlers.abstract_event_handler import (
    AbstractEventHandler,
)
from project.domain import events


class EventHandlerFactory(AbstractEventHandlerFactory):
    def __init__(self, factory_aggregate):
        self.factory_aggregate = factory_aggregate

    def __call__(self, event_type: type[events.Event]) -> list[AbstractEventHandler]:
        try:
            return self.factory_aggregate(event_type)
        except NoSuchProviderError:
            return []
