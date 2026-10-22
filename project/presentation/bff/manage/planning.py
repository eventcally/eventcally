import json

from dependency_injector.wiring import Provide, inject

from project.application.queries import (
    GetSettingsQuery,
    ListAllEventCategoriesQuery,
    ListExternalCalendarEventsQuery,
    PageRequest,
    SearchEventDatesQuery,
)
from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    ExternalCalendarEvent,
    ExternalCalendarEventList,
    ExternalCalendarEventParams,
    PlanningChoice,
    PlanningDistance,
    PlanningEvent,
    PlanningEventDate,
    PlanningEventDateList,
    PlanningEventDateParams,
    PlanningExternalCalendar,
    PlanningOptions,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import can_use_planning
from project.presentation.shared.search_options import distance_choices
from project.shared.dateutils import form_input_to_date
from project.shared.utils import get_event_category_name

MAX_DATES = 200
PAGE_SIZE = 100


def _external_calendars(raw) -> list:
    try:
        calendars = json.loads(raw) if raw else []
        return [
            PlanningExternalCalendar(
                title=c.get("title") or c["url"],
                url=c["url"],
                active=bool(c.get("active", False)),
            )
            for c in calendars
        ]
    except (ValueError, TypeError, KeyError, AttributeError):
        return []


@bff_route(
    bff_manage_bp,
    "/planning",
    response=PlanningOptions,
    summary="Options of the planning calendar",
)
@inject
def get_planning_options(
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    if not can_use_planning():
        raise UnauthorizedError()

    categories = query_bus.handle(ListAllEventCategoriesQuery())
    settings = query_bus.handle(GetSettingsQuery())

    return PlanningOptions(
        categories=sorted(
            [
                PlanningChoice(id=c.id, name=str(get_event_category_name(c)))
                for c in categories
            ],
            key=lambda c: c.name,
        ),
        distances=[
            PlanningDistance(value=value, label=str(label))
            for value, label in distance_choices
        ],
        external_calendars=_external_calendars(settings.planning_external_calendars),
        max_dates=MAX_DATES,
    )


def _has_status_info(event) -> bool:
    if event.public_status and event.public_status != EventPublicStatus.published:
        return True

    return bool(event.status and event.status != EventStatus.scheduled)


def _to_planning_date(hit) -> PlanningEventDate:
    event = hit.event
    return PlanningEventDate(
        id=hit.id,
        start=hit.start,
        end=hit.end,
        allday=hit.allday,
        event=PlanningEvent(
            id=event.id,
            name=event.name,
            status=event.status.name if event.status else None,
            public_status=event.public_status.name,
            booked_up=event.booked_up,
            attendance_mode=(
                event.attendance_mode.name if event.attendance_mode else None
            ),
            has_status_info=_has_status_info(event),
            organization_name=event.admin_unit.name,
            organizer_name=event.organizer.name if event.organizer else None,
            place_name=event.event_place.name if event.event_place else None,
        ),
    )


def _criteria(query: PlanningEventDateParams) -> EventSearchCriteria:
    values = dict(
        date_from=form_input_to_date(query.date_from.isoformat()),
        date_to=form_input_to_date(query.date_to.isoformat(), 23, 59, 59),
        category_ids=query.category_id,
        postal_codes=[query.postal_code] if query.postal_code else [],
        distance=query.distance,
        expected_participants_min=query.expected_participants_min,
        exclude_recurring=query.exclude_recurring,
        public_status=[EventPublicStatus.published, EventPublicStatus.planned],
        include_planned=True,
        include_admin_unit_references=True,
    )

    if query.coordinate:
        latitude, longitude = query.coordinate.split(",")
        values["latitude"] = float(latitude)
        values["longitude"] = float(longitude)

    return EventSearchCriteria(**values)


@bff_route(
    bff_manage_bp,
    "/planning/event-dates",
    query=PlanningEventDateParams,
    response=PlanningEventDateList,
    summary="Published and planned event dates of a date range",
)
@inject
def list_planning_event_dates(
    query: PlanningEventDateParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    if not can_use_planning():
        raise UnauthorizedError()

    criteria = _criteria(query)
    hits = []
    page_number = 1

    while True:
        page = query_bus.handle(
            SearchEventDatesQuery(
                criteria=criteria,
                page=PageRequest(page=page_number, per_page=PAGE_SIZE),
            )
        )
        hits.extend(page.items)

        if not page.has_next or len(hits) >= MAX_DATES:
            break

        page_number += 1

    return PlanningEventDateList(
        items=[_to_planning_date(h) for h in hits[:MAX_DATES]],
        truncated=page.total > MAX_DATES,
    )


def _iso(value) -> str:
    return value.isoformat()


@bff_route(
    bff_manage_bp,
    "/planning/external-calendar-events",
    query=ExternalCalendarEventParams,
    response=ExternalCalendarEventList,
    summary="Events of a configured external calendar",
)
@inject
def list_external_calendar_events(
    query: ExternalCalendarEventParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    if not can_use_planning():
        raise UnauthorizedError()

    events = query_bus.handle(
        ListExternalCalendarEventsQuery(
            url=query.url, date_from=query.date_from, date_to=query.date_to
        )
    )
    return ExternalCalendarEventList(
        url=query.url,
        items=[
            ExternalCalendarEvent(
                name=e.name,
                start=_iso(e.start),
                end=_iso(e.end) if e.end else None,
                allday=e.allday,
                location=e.location,
                description=e.description,
            )
            for e in events
        ],
    )
