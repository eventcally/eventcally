from typing import Optional

from project.domain.events.event_reference_request_auto_verified import (
    EventReferenceRequestAutoVerified,
)
from project.domain.events.event_reference_request_created import (
    EventReferenceRequestCreated,
)
from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)
from project.domain.repositories import AbstractEventReferenceRequestRepository
from project.infrastructure.sql_error_translation import flush
from project.models.event_reference_request import EventReferenceRequest


class SqlAlchemyEventReferenceRequestRepository(
    AbstractEventReferenceRequestRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event_reference_request: EventReferenceRequestAggregate):
        model = EventReferenceRequest.from_aggregate(event_reference_request)
        self.session.add(model)
        flush(self.session)

        event_reference_request.id = model.id

        for event_type in (
            EventReferenceRequestCreated,
            EventReferenceRequestAutoVerified,
        ):
            domain_event = event_reference_request.get_first_domain_event_by_type(
                event_type
            )
            if domain_event:
                domain_event.id = model.id

    def _update(self, event_reference_request: EventReferenceRequestAggregate):
        model = self._get_model(event_reference_request.id)
        model.fill_from_aggregate(event_reference_request)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[EventReferenceRequest]:
        return self.session.query(EventReferenceRequest).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[EventReferenceRequestAggregate]:
        model = self._get_model(object_id)
        return EventReferenceRequest.to_aggregate(model) if model else None

    def _remove(self, event_reference_request: EventReferenceRequestAggregate):
        model = self._get_model(event_reference_request.id)
        self.session.delete(model)
