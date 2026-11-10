from dependency_injector.wiring import Provide, inject
from flask import url_for

from project.application.queries import GetCalendarQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.schemas import (
    PublicCalendar,
    PublicOrganizationRef,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
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
    )
