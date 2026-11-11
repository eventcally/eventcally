from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import ConstraintError, DuplicateError, NotFoundError
from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.enums.event_public_status import EventPublicStatus
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


def ensure_event_may_be_added(event: EventAggregate, admin_unit_id: ObjectId):
    """Own events of any status; foreign ones only when published or planned."""
    if event.admin_unit_id != admin_unit_id and event.public_status not in (
        EventPublicStatus.published,
        EventPublicStatus.planned,
    ):
        raise ConstraintError(
            dummy_gettext(
                "Only published events of other organizations can be added to a calendar"
            )
        )
