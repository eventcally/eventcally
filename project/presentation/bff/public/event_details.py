from dependency_injector.wiring import Provide, inject
from flask import url_for

from project.application.queries import (
    GetEventDateDetailQuery,
    GetEventDetailQuery,
    ListPublicCalendarsForEventQuery,
    ListUpcomingEventDatesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.event_detail_mapping import event_detail
from project.presentation.bff.public.schemas import (
    PublicEventDateDetail,
    PublicEventDetail,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.calendar_access import calendar_organization
from project.presentation.shared.event_links import (
    get_calendar_links_for_event,
    get_calendar_links_for_event_date,
    get_share_links,
)
from project.presentation.shared.event_rights import event_user_rights
from project.presentation.shared.query_results import result_or_404


def _public_calendars(query_bus: QueryBus, event, rights):
    """Only the editors of an event see which public calendars of other
    organizations contain it."""
    if not rights["can_update_event"]:
        return None

    return query_bus.handle(ListPublicCalendarsForEventQuery(event_id=event.id))


@bff_route(
    bff_public_bp,
    "/events/<int:id>",
    response=PublicEventDetail,
    summary="Get event",
)
@inject
def get_event(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=id)))
    rights = event_user_rights(event)
    url = url_for("main.event", event_id=id, _external=True)

    return event_detail(
        event,
        query_bus.handle(ListUpcomingEventDatesQuery(event_id=event.id)),
        rights=rights,
        show_rating=rights["can_update_event"],
        share_links=get_share_links(url, event.name),
        calendar_links=get_calendar_links_for_event(event),
        public_calendars=_public_calendars(query_bus, event, rights),
        calendar_organization=calendar_organization(),
    )


@bff_route(
    bff_public_bp,
    "/event-dates/<int:id>",
    response=PublicEventDateDetail,
    summary="Get event date",
)
@inject
def get_event_date(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event_date = result_or_404(query_bus.handle(GetEventDateDetailQuery(id=id)))
    event = event_date.event
    rights = event_user_rights(event)
    url = url_for("main.event_date", id=id, _external=True)

    return PublicEventDateDetail(
        id=event_date.id,
        start=event_date.start,
        end=event_date.end,
        allday=event_date.allday,
        event=event_detail(
            event,
            query_bus.handle(ListUpcomingEventDatesQuery(event_id=event.id)),
            rights=rights,
            show_rating=False,
            share_links=get_share_links(url, event.name),
            calendar_links=get_calendar_links_for_event_date(event_date),
            public_calendars=_public_calendars(query_bus, event, rights),
            calendar_organization=calendar_organization(),
        ),
    )
