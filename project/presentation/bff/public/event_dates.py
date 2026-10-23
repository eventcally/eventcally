from dependency_injector.wiring import Provide, inject
from flask import abort
from flask_security import current_user

from project.application.queries import (
    GetEventOrganizerQuery,
    GetOrganizationQuery,
    ListAllEventCategoriesQuery,
    SearchEventDatesQuery,
)
from project.application.queries.event_search_criteria import (
    EventSearchCriteria,
    EventSearchSort,
)
from project.application.queries.trackable_criteria import TrackableCriteria
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.event_date_mapping import (
    description_preview,
    photo_of,
)
from project.presentation.bff.public.schemas import (
    EventDateSearchOptions,
    EventDateSearchOptionsParams,
    EventDateSearchParams,
    PublicChoice,
    PublicDistance,
    PublicEventDate,
    PublicEventDateEvent,
    PublicEventDatePage,
    PublicEventDatePlace,
    PublicEventReference,
    PublicOrganizationRef,
    WidgetCategory,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.current_admin_unit import get_current_admin_unit
from project.presentation.shared.search_options import distance_choices
from project.shared.dateutils import form_input_to_date, get_today
from project.shared.utils import get_event_category_name

SORT_CHOICES = [
    ("start", "Earliest start first"),
    ("-created_at", "Newest first"),
]


def _referencing_organization():
    """The session's current organization, if it may reference events."""
    if not current_user or not current_user.is_authenticated:
        return None

    admin_unit = get_current_admin_unit()

    if not admin_unit or not has_access(admin_unit, "incoming_event_references:write"):
        return None

    return admin_unit


def _organization_ref(admin_unit):
    if not admin_unit:
        return None

    return PublicOrganizationRef(id=admin_unit.id, name=admin_unit.name)


@bff_route(
    bff_public_bp,
    "/event-dates/options",
    query=EventDateSearchOptionsParams,
    response=EventDateSearchOptions,
    summary="Options of the event date search",
)
@inject
def get_event_date_search_options(
    query: EventDateSearchOptionsParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organizer = None
    admin_unit = None

    if query.organizer_id:
        organizer = query_bus.handle(GetEventOrganizerQuery(id=query.organizer_id))

        if organizer:
            admin_unit = organizer.admin_unit

    if not admin_unit and query.admin_unit_id:
        admin_unit = query_bus.handle(GetOrganizationQuery(id=query.admin_unit_id))

    categories = query_bus.handle(ListAllEventCategoriesQuery())

    return EventDateSearchOptions(
        default_date_from=get_today().date(),
        categories=sorted(
            [
                WidgetCategory(id=c.id, name=str(get_event_category_name(c)))
                for c in categories
            ],
            key=lambda c: c.name,
        ),
        distances=[
            PublicDistance(value=value, label=str(label))
            for value, label in distance_choices
        ],
        sorts=[PublicChoice(value=v, label=label) for v, label in SORT_CHOICES],
        organization=_organization_ref(admin_unit),
        organizer=_organization_ref(organizer),
        referencing_organization=_organization_ref(_referencing_organization()),
    )


def _reference_of(event, referencing_organization):
    if not referencing_organization:
        return None

    if event.admin_unit_id == referencing_organization.id:
        return PublicEventReference(state="own")

    if event.reference_id:
        return PublicEventReference(state="referenced", reference_id=event.reference_id)

    return PublicEventReference(state="none")


def _place_of(event):
    place = event.event_place

    if not place:
        return None

    location = place.location
    has_coordinate = (
        location is not None
        and location.latitude is not None
        and location.longitude is not None
    )

    return PublicEventDatePlace(
        name=place.name,
        latitude=float(location.latitude) if has_coordinate else None,
        longitude=float(location.longitude) if has_coordinate else None,
    )


def _to_event_date(hit, referencing_organization) -> PublicEventDate:
    event = hit.event
    return PublicEventDate(
        id=hit.id,
        start=hit.start,
        end=hit.end,
        allday=hit.allday,
        event=PublicEventDateEvent(
            id=event.id,
            name=event.name,
            description_preview=description_preview(event.description),
            status=event.status.name if event.status else None,
            public_status=event.public_status.name,
            booked_up=event.booked_up,
            attendance_mode=(
                event.attendance_mode.name if event.attendance_mode else None
            ),
            organization=PublicOrganizationRef(
                id=event.admin_unit.id, name=event.admin_unit.name
            ),
            organizer_name=event.organizer.name if event.organizer else None,
            place=_place_of(event),
            photo=photo_of(event.photo),
            reference=_reference_of(event, referencing_organization),
        ),
    )


def _split(value):
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def _criteria(query: EventDateSearchParams, referencing_organization):
    criteria = dict(
        date_from=form_input_to_date((query.date_from or get_today()).isoformat()[:10]),
        date_to=(
            form_input_to_date(query.date_to.isoformat(), 23, 59, 59)
            if query.date_to
            else None
        ),
        trackable=TrackableCriteria(
            created_at_from=(
                form_input_to_date(query.created_at_from.isoformat())
                if query.created_at_from
                else None
            ),
            created_at_to=(
                form_input_to_date(query.created_at_to.isoformat(), 23, 59, 59)
                if query.created_at_to
                else None
            ),
        ),
        keyword=(query.keyword or "").strip() or None,
        category_ids=[c for c in query.category_id if c > 0],
        tags=_split(query.tag),
        postal_codes=_split(query.postal_code),
        admin_unit_id=query.admin_unit_id,
        organizer_id=query.organizer_id,
        exclude_recurring=query.exclude_recurring,
        sort=EventSearchSort(query.sort),
        include_planned=True,
        include_admin_unit_references=True,
    )

    if query.coordinate:
        criteria["latitude"], criteria["longitude"] = query.coordinate.split(",")
        criteria["distance"] = query.distance

    if referencing_organization and query.not_referenced:
        criteria["not_referenced_by_admin_unit_id"] = referencing_organization.id

    return EventSearchCriteria(**criteria)


@bff_route(
    bff_public_bp,
    "/event-dates",
    query=EventDateSearchParams,
    response=PublicEventDatePage,
    summary="Search event dates",
)
@inject
def search_event_dates(
    query: EventDateSearchParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    referencing_organization = _referencing_organization()
    page = query_bus.handle(
        SearchEventDatesQuery(
            criteria=_criteria(query, referencing_organization),
            reference_admin_unit_id=(
                referencing_organization.id if referencing_organization else None
            ),
            page=query.to_page_request(),
        )
    )

    if page.is_out_of_range:
        abort(404)

    return PublicEventDatePage(
        items=[_to_event_date(h, referencing_organization) for h in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
    )
