from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)


def ensure_event_reference_exists(
    event_reference_id: int, uow: AbstractUnitOfWork
) -> EventReferenceAggregate:
    event_reference = uow.event_references.get(event_reference_id)

    if not event_reference:  # pragma: no cover
        raise NotFoundError(f"Event reference with id {event_reference_id} not found")

    return event_reference
