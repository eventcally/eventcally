from dependency_injector.wiring import Provide, inject
from flask import current_app, render_template, url_for
from flask.wrappers import Response
from flask_babel import gettext

from project.application.queries import (
    GetEventDateDetailQuery,
    ListUpcomingEventDatesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.ical import create_ical_event_for_date
from project.presentation.web.jsonld import get_sd_for_event_date
from project.presentation.web.views.event import get_user_rights
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import (
    get_calendar_links_for_event_date,
    get_meta_data,
    get_share_links,
)
from project.shared.dateutils import create_icalendar


@main_bp.route("/eventdates")
def event_dates():
    return render_template(
        "layout_vue3.html",
        entry="public",
        title=gettext("Event Dates"),
        boot=build_boot_data(base="/"),
    )


@main_bp.route("/eventdate/<int:id>")
@inject
def event_date(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event_date = result_or_404(query_bus.handle(GetEventDateDetailQuery(id=id)))

    structured_data = current_app.json.dumps(
        get_sd_for_event_date(event_date), indent=2
    )

    url = url_for("main.event_date", id=id, _external=True)
    share_links = get_share_links(url, event_date.event.name)
    calendar_links = get_calendar_links_for_event_date(event_date)

    return render_template(
        "event_date/read.html",
        event_date=event_date,
        structured_data=structured_data,
        meta=get_meta_data(event_date.event, event_date),
        canonical_url=url_for("main.event_date", id=id, _external=True),
        user_rights=get_user_rights(event_date.event),
        dates=query_bus.handle(
            ListUpcomingEventDatesQuery(event_id=event_date.event.id)
        ),
        share_links=share_links,
        calendar_links=calendar_links,
    )


@main_bp.route("/eventdate/<int:id>/ical")
@inject
def event_date_ical(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event_date = result_or_404(query_bus.handle(GetEventDateDetailQuery(id=id)))
    event = create_ical_event_for_date(event_date)

    cal = create_icalendar()
    cal.add_component(event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=eventdate_{id}.ics"},
    )
