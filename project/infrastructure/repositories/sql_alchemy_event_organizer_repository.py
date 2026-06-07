from typing import Optional

from project.domain.events.event_organizer_created import EventOrganizerCreated
from project.domain.events.event_organizer_updated import EventOrganizerUpdated
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.repositories import AbstractEventOrganizerRepository
from project.models.event_organizer import EventOrganizer


class SqlAlchemyEventOrganizerRepository(AbstractEventOrganizerRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event_organizer: EventOrganizerAggregate):
        model = EventOrganizer.from_aggregate(event_organizer)
        self.session.add(model)
        self.session.flush()

        domain_event = event_organizer.get_first_domain_event_by_type(
            EventOrganizerCreated
        )
        event_organizer.id = model.id
        domain_event.id = model.id

        if model.logo:
            event_organizer.logo.id = model.logo.id
            domain_event.logo.id = model.logo.id
            domain_event.logo.hash = model.logo.get_hash()

    def _update(self, event_organizer: EventOrganizerAggregate):
        model = self._get_model(event_organizer.id)
        model.fill_from_aggregate(event_organizer)
        self.session.merge(model)
        self.session.flush()

        if model.logo:
            event_organizer.logo.id = model.logo.id

            domain_event = event_organizer.get_first_domain_event_by_type(
                EventOrganizerUpdated
            )
            domain_event.logo.new.id = model.logo.id
            domain_event.logo.new.hash = model.logo.get_hash()

    def _get_model(self, object_id: int) -> Optional[EventOrganizer]:
        return self.session.query(EventOrganizer).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[EventOrganizerAggregate]:
        model = self._get_model(object_id)
        return EventOrganizer.to_aggregate(model) if model else None

    def _remove(self, event_organizer: EventOrganizerAggregate):
        model = self._get_model(event_organizer.id)
        self.session.delete(model)
