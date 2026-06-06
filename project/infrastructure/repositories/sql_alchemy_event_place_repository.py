from typing import Optional

from project.domain.events.event_place_created import EventPlaceCreated
from project.domain.events.event_place_updated import EventPlaceUpdated
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.repositories import AbstractEventPlaceRepository
from project.models.event_place import EventPlace


class SqlAlchemyEventPlaceRepository(AbstractEventPlaceRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event_place: EventPlaceAggregate):
        model = EventPlace.from_aggregate(event_place)
        self.session.add(model)
        self.session.flush()

        domain_event = event_place.get_first_domain_event_by_type(EventPlaceCreated)
        event_place.id = model.id
        domain_event.id = model.id

        if model.photo:
            event_place.photo.id = model.photo.id
            domain_event.photo.id = model.photo.id
            domain_event.photo.hash = model.photo.get_hash()

    def _update(self, event_place: EventPlaceAggregate):
        model = self._get_model(event_place.id)
        model.fill_from_aggregate(event_place)
        self.session.merge(model)
        self.session.flush()

        if model.photo:
            event_place.photo.id = model.photo.id

            domain_event = event_place.get_first_domain_event_by_type(EventPlaceUpdated)
            domain_event.photo.new.id = model.photo.id
            domain_event.photo.new.hash = model.photo.get_hash()

    def _get_model(self, object_id: int) -> Optional[EventPlace]:
        return self.session.query(EventPlace).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[EventPlaceAggregate]:
        model = self._get_model(object_id)
        return EventPlace.to_aggregate(model)

    def _remove(self, event_place: EventPlaceAggregate):
        model = self._get_model(event_place.id)
        self.session.delete(model)
