from typing import Optional

from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.repositories.abstract_event_reference_repository import (
    AbstractEventReferenceRepository,
)
from project.infrastructure.sql_error_translation import flush
from project.models.event_reference import EventReference


class SqlAlchemyEventReferenceRepository(AbstractEventReferenceRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_by_event_id(self, event_id: int) -> list[EventReferenceAggregate]:
        event_references = (
            self.session.query(EventReference).filter_by(event_id=event_id).all()
        )
        return [EventReference.to_aggregate(er) for er in event_references]

    def _add(self, event_reference: EventReferenceAggregate):
        model = EventReference.from_aggregate(event_reference)
        self.session.add(model)
        flush(self.session)

        event_reference.id = model.id

    def _update(self, event_reference: EventReferenceAggregate):
        model = self._get_model(event_reference.id)
        model.fill_from_aggregate(event_reference)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[EventReference]:
        return self.session.query(EventReference).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[EventReferenceAggregate]:
        model = self._get_model(object_id)
        return EventReference.to_aggregate(model) if model else None

    def _remove(self, event_reference: EventReferenceAggregate):
        model = self._get_model(event_reference.id)
        self.session.delete(model)
