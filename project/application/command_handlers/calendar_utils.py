from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import DuplicateError, NotFoundError
from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.translation import dummy_gettext
from project.domain.types import ObjectId


def ensure_calendar_exists(
    calendar_id: ObjectId, uow: AbstractUnitOfWork
) -> CalendarAggregate:
    calendar = uow.calendars.get(calendar_id)

    if not calendar:
        raise NotFoundError(dummy_gettext("Calendar not found"))

    return calendar


def ensure_calendar_name_is_free(
    admin_unit_id: ObjectId,
    name: str,
    uow: AbstractUnitOfWork,
    exclude_id: ObjectId | None = None,
):
    other = uow.calendars.get_by_admin_unit_and_name(admin_unit_id, name.strip())

    if other and other.id != exclude_id:
        raise DuplicateError(dummy_gettext("A calendar already exists with this name."))
