from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.repositories.abstract_event_reference_repository import (
    AbstractEventReferenceRepository,
)
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
