from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)


def ensure_event_organizer_exists(
    event_organizer_id: int, uow: AbstractUnitOfWork
) -> EventOrganizerAggregate:
    event_organizer = uow.event_organizers.get(event_organizer_id)

    if not event_organizer:  # pragma: no cover
        raise NotFoundError(f"Event organizer with id {event_organizer_id} not found")

    return event_organizer
