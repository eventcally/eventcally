from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)
from project.domain.models.entities.actor import Actor


def ensure_event_reference_request_exists(
    event_reference_request_id: int, uow: AbstractUnitOfWork
) -> EventReferenceRequestAggregate:
    event_reference_request = uow.event_reference_requests.get(
        event_reference_request_id
    )

    if not event_reference_request:
        raise NotFoundError(
            f"Event reference request with id {event_reference_request_id} not found"
        )

    return event_reference_request


def create_event_reference_for_request(
    uow: AbstractUnitOfWork,
    actor: Actor,
    event_reference_request: EventReferenceRequestAggregate,
    rating: int = 50,
) -> EventReferenceAggregate:
    """Create the `EventReference` a verified/auto-verified request grants.

    Mirrors `CreateEventReferenceHandler.handle` (the already-migrated
    sibling aggregate) minus the permission check — the caller already
    checked its own permission for `event_reference_request.admin_unit_id` —
    called directly against the shared `uow` rather than dispatched as a
    nested command (which would open a second transaction).
    """
    event_reference = EventReferenceAggregate.create(
        actor=actor,
        admin_unit_id=event_reference_request.admin_unit_id,
        event_id=event_reference_request.event_id,
        rating=rating,
    )
    uow.event_references.add(event_reference)
    return event_reference
