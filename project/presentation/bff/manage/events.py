from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import DeleteEventCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    EventSearchCriteria,
    EventSearchSort,
    GetEventForEditQuery,
    GetEventOrganizerRefQuery,
    GetEventPlaceRefQuery,
    ListAllEventCategoriesQuery,
    LookupEventOrganizersQuery,
    LookupEventPlacesQuery,
    PageRequest,
    SearchEventsQuery,
    TrackableCriteria,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.event_dates import collect_event_dates
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    EventDeleted,
    EventDeleteForm,
    EventDeleteSave,
    ManageChoice,
    ManageEventDate,
    ManageEventDateEvent,
    ManageEventDateList,
    ManageEventDateParams,
    ManageEventListItem,
    ManageEventListOptions,
    ManageEventListParams,
    ManageEventPage,
    ManageRef,
    ManageRefList,
    ManageRefParams,
    PlanningChoice,
    PlanningDistance,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import (
    can_request_event_reference_from_admin_unit,
    get_admin_unit_for_manage,
    has_access,
)
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.search_options import distance_choices
from project.shared.dateutils import form_input_to_date, get_today
from project.shared.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_place_str,
)

PER_PAGE = 50
MAX_DATES = 500
LOOKUP_PER_PAGE = 10

_SORTS = {
    "-last_modified_at": EventSearchSort.last_modified_at_desc,
    "-created_at": EventSearchSort.created_at_desc,
}


def _authorize(id: int) -> None:
    if not has_access(SimpleNamespace(id=id), "events:read"):
        raise UnauthorizedError()


def _split(value) -> list:
    return [item for item in value.split(",") if item] if value else []


def _start_of_day(value, end_of_day=False):
    if not value:
        return None

    if end_of_day:
        return form_input_to_date(value.isoformat(), 23, 59, 59)

    return form_input_to_date(value.isoformat())


def _criteria(id: int, query: ManageEventListParams) -> EventSearchCriteria:
    latitude = longitude = distance = None

    if query.radius_coordinate and query.radius_distance:
        latitude, longitude = query.radius_coordinate.split(",")
        distance = query.radius_distance

    date_from = _start_of_day(query.date_from) or get_today()
    status = EventStatus(query.status) if query.status else None
    public_status = (
        EventPublicStatus(query.public_status) if query.public_status else None
    )

    return EventSearchCriteria(
        admin_unit_id=id,
        include_private=True,
        name=query.keyword or None,
        date_from=date_from,
        date_to=_start_of_day(query.date_to, end_of_day=True),
        category_ids=[query.category_id] if query.category_id else [],
        tags=_split(query.tag),
        internal_tags=_split(query.internal_tag),
        organizer_id=query.organizer_id,
        event_place_id=query.event_place_id,
        postal_codes=_split(query.postal_code),
        latitude=latitude,
        longitude=longitude,
        distance=distance,
        status=[status] if status else [],
        public_status=[public_status] if public_status else [],
        is_recurring={"1": True, "0": False}.get(query.is_recurring),
        trackable=TrackableCriteria(
            created_at_from=_start_of_day(query.created_at_from),
            created_at_to=_start_of_day(query.created_at_to, end_of_day=True),
        ),
        sort=_SORTS.get(query.sort),
    )


def _place_label(place) -> str:
    if not place:
        return None

    parts = [place.name]
    location = place.location

    if location:
        if location.postalCode:
            parts.append(location.postalCode)
        if location.city:
            parts.append(location.city)

    return " ".join(parts)


def to_item(event) -> ManageEventListItem:
    definition = event.min_start_definition

    return ManageEventListItem(
        id=event.id,
        name=event.name,
        start=definition.start if definition else None,
        allday=definition.allday if definition else False,
        is_recurring=event.is_recurring,
        number_of_dates=event.number_of_dates,
        organizer_name=event.organizer.name if event.organizer else None,
        place_label=_place_label(event.event_place),
        category_names=[str(get_event_category_name(c)) for c in event.categories],
        tags=event.tags,
        internal_tags=event.internal_tags,
        status=event.status.name if event.status else None,
        public_status=event.public_status.name,
        has_photo=event.photo is not None,
        number_of_references=event.number_of_references,
        number_of_reference_requests=event.number_of_reference_requests,
        last_modified_at=event.last_modified_at,
    )


def _choices(enum) -> list:
    return [
        ManageChoice(
            value=int(member),
            name=member.name,
            label=str(get_localized_enum_name(member)),
        )
        for member in enum
    ]


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/options",
    response=ManageEventListOptions,
    summary="Filter options of the event list of an organization",
)
@inject
def get_event_list_options(
    id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _authorize(id)
    categories = query_bus.handle(ListAllEventCategoriesQuery())
    admin_unit = get_admin_unit_for_manage(id)

    return ManageEventListOptions(
        categories=sorted(
            [
                PlanningChoice(id=c.id, name=str(get_event_category_name(c)))
                for c in categories
            ],
            key=lambda c: c.name,
        ),
        statuses=_choices(EventStatus),
        public_statuses=_choices(EventPublicStatus),
        distances=[
            PlanningDistance(value=value, label=str(label))
            for value, label in distance_choices
        ],
        default_date_from=get_today().date(),
        can_write=has_access(SimpleNamespace(id=id), "events:write"),
        can_request_reference=bool(
            admin_unit and can_request_event_reference_from_admin_unit(admin_unit)
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events",
    query=ManageEventListParams,
    response=ManageEventPage,
    summary="Search the events of an organization",
)
@inject
def list_events(
    id: int,
    query: ManageEventListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _authorize(id)
    page = query_bus.handle(
        SearchEventsQuery(
            criteria=_criteria(id, query),
            reference_admin_unit_id=id,
            include_counts=True,
            page=PageRequest(page=query.page, per_page=PER_PAGE),
        )
    )

    organizer = place = None

    if query.organizer_id:
        found = query_bus.handle(
            GetEventOrganizerRefQuery(admin_unit_id=id, id=query.organizer_id)
        )
        organizer = ManageRef(id=found.id, name=found.name) if found else None

    if query.event_place_id:
        found = query_bus.handle(
            GetEventPlaceRefQuery(admin_unit_id=id, id=query.event_place_id)
        )
        place = ManageRef(id=found.id, name=get_place_str(found)) if found else None

    return ManageEventPage(
        items=[to_item(e) for e in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        organizer=organizer,
        event_place=place,
    )


def to_date_item(hit) -> ManageEventDate:
    event = hit.event

    return ManageEventDate(
        id=hit.id,
        start=hit.start,
        end=hit.end,
        allday=hit.allday,
        event=ManageEventDateEvent(
            id=event.id,
            name=event.name,
            is_recurring=event.is_recurring,
            status=event.status.name if event.status else None,
            public_status=event.public_status.name,
            organizer_name=event.organizer.name if event.organizer else None,
            place_label=_place_label(event.event_place),
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-dates",
    query=ManageEventDateParams,
    response=ManageEventDateList,
    summary="Event dates of the events of an organization in a date range",
)
@inject
def list_event_dates(
    id: int,
    query: ManageEventDateParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _authorize(id)
    # The calendar shows the dates in start order, whatever the list sorts by.
    criteria = _criteria(id, query).model_copy(update={"sort": None})
    hits, truncated = collect_event_dates(query_bus, criteria, MAX_DATES)

    return ManageEventDateList(
        items=[to_date_item(h) for h in hits], truncated=truncated
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-organizers",
    query=ManageRefParams,
    response=ManageRefList,
    summary="Look up the event organizers of an organization",
)
@inject
def lookup_event_organizers(
    id: int,
    query: ManageRefParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _authorize(id)
    page = query_bus.handle(
        LookupEventOrganizersQuery(
            admin_unit_id=id,
            term=query.keyword,
            page=PageRequest(page=1, per_page=LOOKUP_PER_PAGE),
        )
    )
    return ManageRefList(items=[ManageRef(id=o.id, name=o.name) for o in page.items])


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-places",
    query=ManageRefParams,
    response=ManageRefList,
    summary="Look up the event places of an organization",
)
@inject
def lookup_event_places(
    id: int,
    query: ManageRefParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _authorize(id)
    page = query_bus.handle(
        LookupEventPlacesQuery(
            admin_unit_id=id,
            term=query.keyword,
            page=PageRequest(page=1, per_page=LOOKUP_PER_PAGE),
        )
    )
    return ManageRefList(
        items=[ManageRef(id=p.id, name=get_place_str(p)) for p in page.items]
    )


def _event_for_delete_or_404(id: int, event_id: int, query_bus: QueryBus):
    if not has_access(SimpleNamespace(id=id), "events:write"):
        raise UnauthorizedError()

    try:
        event = result_or_404(query_bus.handle(GetEventForEditQuery(id=event_id)))
    except UnauthorizedError:
        # An event the actor may not read (e.g. a draft of another organization).
        abort(404)

    # Do not reveal the events of other organizations.
    if event.admin_unit_id != id:
        abort(404)

    return event


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/delete-form",
    response=EventDeleteForm,
    summary="Get what the event delete confirmation shows",
)
@inject
def get_event_delete_form(
    id: int,
    event_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    event = _event_for_delete_or_404(id, event_id, query_bus)
    return EventDeleteForm(
        id=event.id, name=event.name, has_multiple_dates=event.has_multiple_dates()
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/delete",
    method="POST",
    body=EventDeleteSave,
    response=EventDeleted,
    summary="Delete an event",
)
@inject
def delete_event(
    id: int,
    event_id: int,
    body: EventDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _event_for_delete_or_404(id, event_id, query_bus)
    message_bus.handle_command(DeleteEventCommand(actor=actor(), id=event_id))
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=gettext("Event"),
    )

    if not body.inline:
        flash(message, "success")

    return EventDeleted(
        message=message, redirect_url=url_for("manage_admin_unit.events", id=id)
    )
