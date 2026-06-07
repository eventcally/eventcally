from typing import Optional

from project.domain.events.event_created import EventCreated
from project.domain.events.event_updated import EventUpdated
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.repositories.abstract_event_repository import (
    AbstractEventRepository,
)
from project.models.event import Event


class SqlAlchemyEventRepository(AbstractEventRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event: EventAggregate):
        model = Event.from_aggregate(event)
        self.session.add(model)
        self.session.flush()

        domain_event = event.get_first_domain_event_by_type(EventCreated)
        event.id = model.id
        domain_event.id = model.id

        if model.photo:
            event.photo.id = model.photo.id
            domain_event.photo.id = model.photo.id
            domain_event.photo.hash = model.photo.get_hash()

    def _update(self, event: EventAggregate):
        model = self._get_model(event.id)
        model.fill_from_aggregate(event)
        self.session.merge(model)
        self.session.flush()

        if model.photo:
            event.photo.id = model.photo.id

            domain_event = event.get_first_domain_event_by_type(EventUpdated)
            domain_event.photo.new.id = model.photo.id
            domain_event.photo.new.hash = model.photo.get_hash()

    def _get_model(self, object_id: int) -> Optional[Event]:
        return self.session.query(Event).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[EventAggregate]:
        model = self._get_model(object_id)
        return Event.to_aggregate(model) if model else None

    def _remove(self, event: EventAggregate):
        model = self._get_model(event.id)
        self.session.delete(model)
