from typing import List, Optional

from project.domain.events.base import Event, TEvent
from project.domain.types.custom_base_model import CustomBaseModel


class BaseAggregate(CustomBaseModel):
    __hash__ = object.__hash__  # use object identity for hashing
    domain_events: List[Event] = []

    def get_first_domain_event_by_type(
        self, event_type: type[TEvent]
    ) -> Optional[TEvent]:
        for event in self.domain_events:
            if isinstance(event, event_type):
                return event
        return None  # pragma: no cover
