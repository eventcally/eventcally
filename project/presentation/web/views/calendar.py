from dateutil.relativedelta import relativedelta
from dependency_injector.wiring import Provide, inject
from flask import Response, abort, render_template, url_for

from project.application.queries import (
    EventSearchCriteria,
    GetCalendarQuery,
    ListAllEventsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.ical import create_ical_events_for_events
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import truncate
from project.shared.dateutils import create_icalendar, get_today


@main_bp.route("/calendars/<int:id>")
@inject
def calendar(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    # A private calendar answers None (404) unless the user has calendars:read.
    calendar = result_or_404(query_bus.handle(GetCalendarQuery(id=id)))
    meta = dict(
        description=(
            truncate(calendar.description, 300)
            if calendar.description
            else f"{calendar.name} – {calendar.admin_unit.name}"
        )
    )

    return render_template(
        "layout_vue3.html",
        entry="public",
        title=calendar.name,
        boot=build_boot_data(base="/"),
        meta=meta,
        canonical_url=url_for("main.calendar", id=id, _external=True),
    )


@main_bp.route("/calendars/<int:id>/ical")
@inject
def calendar_ical(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    calendar = result_or_404(query_bus.handle(GetCalendarQuery(id=id)))

    # Feeds are anonymous by nature: a private calendar has none, whoever asks.
    if calendar.private:
        abort(404)

    cal = create_icalendar()
    cal.add("x-wr-calname", calendar.name)
    # No organization and no private flags: only public statuses of verified
    # organizations, like the public search.
    events = query_bus.handle(
        ListAllEventsQuery(
            criteria=EventSearchCriteria(
                calendar_ids=[id], date_from=get_today() - relativedelta(months=1)
            )
        )
    )

    for ical_event in create_ical_events_for_events(events):
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=calendar_{id}.ics"},
    )
