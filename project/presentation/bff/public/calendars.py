from dependency_injector.wiring import Provide, inject
from flask import url_for

from project.application.queries import GetCalendarQuery, LookupPublicCalendarsQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.schemas import (
    PublicCalendar,
    PublicCalendarLookup,
    PublicCalendarLookupParams,
    PublicCalendarRef,
    PublicOrganizationRef,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.calendar_access import calendar_organization
from project.presentation.shared.query_results import result_or_404


@bff_route(
    bff_public_bp,
    "/calendars/<int:id>",
    response=PublicCalendar,
    summary="Get calendar",
)
@inject
def get_calendar(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    # A private calendar answers None (404) unless the user has calendars:read.
    calendar = result_or_404(query_bus.handle(GetCalendarQuery(id=id)))
    organization = calendar.admin_unit
    can_manage = has_access(organization, "calendars:write")

    return PublicCalendar(
        id=calendar.id,
        name=calendar.name,
        description=calendar.description,
        private=calendar.private,
        organization=PublicOrganizationRef(id=organization.id, name=organization.name),
        ical_url=url_for("main.calendar_ical", id=calendar.id, _external=True),
        manage_url=(
            url_for(
                "manage_admin_unit.calendar_update",
                id=organization.id,
                calendar_id=calendar.id,
            )
            if can_manage
            else None
        ),
        calendar_organization=_organization_ref(calendar_organization()),
    )


def _organization_ref(admin_unit):
    if not admin_unit:
        return None

    return PublicOrganizationRef(id=admin_unit.id, name=admin_unit.name)


@bff_route(
    bff_public_bp,
    "/calendars",
    query=PublicCalendarLookupParams,
    response=PublicCalendarLookup,
    summary="Find public calendars by calendar or organization name",
)
@inject
def lookup_calendars(
    query: PublicCalendarLookupParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    calendars = query_bus.handle(
        LookupPublicCalendarsQuery(keyword=query.keyword, limit=query.per_page)
    )

    return PublicCalendarLookup(
        items=[
            PublicCalendarRef(
                id=c.id,
                name=c.name,
                organization=PublicOrganizationRef(
                    id=c.organization.id, name=c.organization.name
                ),
            )
            for c in calendars
        ]
    )
