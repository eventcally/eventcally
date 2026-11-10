from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateCalendarCommand,
    DeleteCalendarCommand,
    SetEventCalendarsCommand,
    UpdateCalendarCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    CalendarSort,
    GetCalendarQuery,
    GetEventDetailQuery,
    IsCalendarNameTakenQuery,
    ListCalendarsQuery,
    ListEventCalendarIdsQuery,
    PageRequest,
)
from project.application.queries.page_request import MAX_PER_PAGE
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    CalendarChoice,
    CalendarChoices,
    CalendarForm,
    CalendarListItem,
    CalendarListPage,
    CalendarNameAvailability,
    CalendarNameAvailabilityParams,
    CalendarSave,
    CalendarSaved,
    EventCalendars,
    EventCalendarsSave,
    ManageMessage,
    ManageNameConfirm,
    ManageNamedListParams,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.shared.utils import strings_are_equal_ignoring_case


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _calendar_or_404(id: int, calendar_id: int, query_bus: QueryBus, permission: str):
    _access_or_forbidden(id, permission)
    calendar = result_or_404(query_bus.handle(GetCalendarQuery(id=calendar_id)))

    # Do not reveal the calendars of other organizations.
    if calendar.admin_unit_id != id:
        abort(404)

    return calendar


def calendar_choices(query_bus: QueryBus, id: int) -> list:
    """The organization's calendars; none without `calendars:read`."""
    if not has_access(SimpleNamespace(id=id), "calendars:read"):
        return []

    choices = []
    number = 1

    while True:
        page = query_bus.handle(
            ListCalendarsQuery(
                admin_unit_id=id,
                sort=CalendarSort.name,
                page=PageRequest(page=number, per_page=MAX_PER_PAGE),
            )
        )
        choices.extend(
            CalendarChoice(id=c.id, name=c.name, private=c.private) for c in page.items
        )

        if number >= page.pages:
            return choices

        number += 1


def _readable_event_or_404(event_id: int, query_bus: QueryBus):
    """Calendars hold own and foreign events: the event must be readable for the user
    (an event the actor may not read answers like a missing one)."""
    try:
        result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))
    except UnauthorizedError:
        abort(404)


def _name_errors(query_bus: QueryBus, id: int, name: str, exclude_id=None) -> list:
    if query_bus.handle(
        IsCalendarNameTakenQuery(admin_unit_id=id, name=name, exclude_id=exclude_id)
    ):
        return [(["name"], gettext("A calendar already exists with this name."))]

    return []


def _saved(id: int, calendar_id: int, text: str, inline=False) -> CalendarSaved:
    if not inline:
        flash(text, "success")

    return CalendarSaved(
        id=calendar_id,
        redirect_url=url_for("manage_admin_unit.calendars", id=id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/create-form",
    response=CalendarForm,
    summary="Get the form to create a calendar",
)
def get_calendar_create_form(id: int):
    _access_or_forbidden(id, "calendars:write")
    return CalendarForm()


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/choices",
    response=CalendarChoices,
    summary="The calendars of an organization for the calendar picker",
)
@inject
def get_calendar_choices(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    _access_or_forbidden(id, "calendars:read")
    return CalendarChoices(items=calendar_choices(query_bus, id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/name-availability",
    query=CalendarNameAvailabilityParams,
    response=CalendarNameAvailability,
    summary="Whether the name of a calendar is taken",
)
@inject
def get_calendar_name_availability(
    id: int,
    query: CalendarNameAvailabilityParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "calendars:write")
    result = CalendarNameAvailability()

    if query.name:
        result.name_taken = query_bus.handle(
            IsCalendarNameTakenQuery(
                admin_unit_id=id, name=query.name, exclude_id=query.exclude_id
            )
        )

    return result


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/list",
    query=ManageNamedListParams,
    response=CalendarListPage,
    summary="List the calendars of an organization",
)
@inject
def list_calendars(
    id: int,
    query: ManageNamedListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "calendars:read")

    page = result_or_404(
        query_bus.handle(
            ListCalendarsQuery(
                admin_unit_id=id,
                keyword=query.keyword or None,
                sort=CalendarSort(query.sort or "name"),
                page=query.to_page_request(),
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return CalendarListPage(
        items=[
            CalendarListItem(
                id=c.id,
                name=c.name,
                description=c.description,
                private=c.private,
                number_of_events=c.number_of_events,
                last_modified_at=c.last_modified_at,
                public_url=(None if c.private else f"/calendars/{c.id}"),
            )
            for c in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "calendars:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/<int:calendar_id>",
    response=CalendarForm,
    summary="Get the form to update a calendar",
)
@inject
def get_calendar_form(
    id: int,
    calendar_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    calendar = _calendar_or_404(id, calendar_id, query_bus, "calendars:write")

    return CalendarForm(
        id=calendar.id,
        name=calendar.name,
        description=calendar.description,
        private=calendar.private,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars",
    method="POST",
    body=CalendarSave,
    response=CalendarSaved,
    status=201,
    summary="Create a calendar",
)
@inject
def create_calendar(
    id: int,
    body: CalendarSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "calendars:write")
    errors = _name_errors(query_bus, id, body.name)

    if errors:
        raise FieldValidationError(errors=errors)

    result = message_bus.handle_command(
        CreateCalendarCommand(
            actor=actor(),
            admin_unit_id=id,
            name=body.name,
            description=body.description,
            private=body.private,
        )
    )

    return _saved(
        id,
        result.id,
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=gettext("Calendar"),
        ),
        inline=body.inline,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/<int:calendar_id>",
    method="PUT",
    body=CalendarSave,
    response=CalendarSaved,
    summary="Update a calendar",
)
@inject
def update_calendar(
    id: int,
    calendar_id: int,
    body: CalendarSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _calendar_or_404(id, calendar_id, query_bus, "calendars:write")
    errors = _name_errors(query_bus, id, body.name, exclude_id=calendar_id)

    if errors:
        raise FieldValidationError(errors=errors)

    message_bus.handle_command(
        UpdateCalendarCommand(
            actor=actor(),
            id=calendar_id,
            name=body.name,
            description=body.description,
            private=body.private,
        )
    )

    return _saved(
        id,
        calendar_id,
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=gettext("Calendar"),
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/calendars/<int:calendar_id>/delete",
    method="POST",
    body=ManageNameConfirm,
    response=ManageMessage,
    summary="Delete a calendar after typing its name",
)
@inject
def delete_calendar(
    id: int,
    calendar_id: int,
    body: ManageNameConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    calendar = _calendar_or_404(id, calendar_id, query_bus, "calendars:write")

    if not strings_are_equal_ignoring_case(body.name, calendar.name):
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match calendar name")
        )

    message_bus.handle_command(DeleteCalendarCommand(actor=actor(), id=calendar_id))

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully deleted",
            model_display_name=gettext("Calendar"),
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/calendars",
    response=EventCalendars,
    summary="The calendars of an organization and those the event is in",
)
@inject
def get_event_calendars(
    id: int,
    event_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "calendars:read")
    _readable_event_or_404(event_id, query_bus)

    return EventCalendars(
        choices=calendar_choices(query_bus, id),
        selected_ids=query_bus.handle(
            ListEventCalendarIdsQuery(admin_unit_id=id, event_id=event_id)
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/calendars",
    method="PUT",
    body=EventCalendarsSave,
    response=ManageMessage,
    summary="Put an event into calendars of an organization",
)
@inject
def put_event_calendars(
    id: int,
    event_id: int,
    body: EventCalendarsSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "calendars:write")
    _readable_event_or_404(event_id, query_bus)
    ensure_calendars_are_choices(query_bus, id, body.calendar_ids)

    message_bus.handle_command(
        SetEventCalendarsCommand(
            actor=actor(),
            admin_unit_id=id,
            event_id=event_id,
            calendar_ids=body.calendar_ids,
        )
    )

    return ManageMessage(message=gettext("Calendars successfully saved"))


def ensure_calendars_are_choices(query_bus: QueryBus, id: int, calendar_ids: list):
    """Reject ids of other organizations before the event command runs, so the
    calendar command cannot fail on input afterwards."""
    allowed = {c.id for c in calendar_choices(query_bus, id)}

    if not set(calendar_ids) <= allowed:
        raise FieldValidationError(["calendar_ids"], gettext("Calendar not found"))
