from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_aggregate import EventAggregate


def ensure_event_exists(event_id: int, uow: AbstractUnitOfWork) -> EventAggregate:
    event = uow.events.get(event_id)

    if not event:
        raise NotFoundError(f"Event with id {event_id} not found")

    return event
