from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.models import EventPlace


def ensure_event_place_exists(
    event_place_id: int, uow: AbstractUnitOfWork
) -> EventPlace:
    event_place = uow.event_places.get(event_place_id)

    if not event_place:
        raise NotFoundError(f"Event place with id {event_place_id} not found")

    return event_place
