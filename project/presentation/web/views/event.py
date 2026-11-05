from dependency_injector.wiring import Provide, inject
from flask import Response, current_app, render_template, url_for
from flask_babel import gettext

from project.application.queries import GetEventDetailQuery, ListUpcomingEventDatesQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.ical import create_ical_events_for_event
from project.presentation.web.jsonld import get_sd_for_event_date
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import get_meta_data
from project.shared.dateutils import create_icalendar


@main_bp.route("/event/<int:event_id>")
@inject
def event(event_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))
    dates = query_bus.handle(ListUpcomingEventDatesQuery(event_id=event.id))

    structured_datas = list()
    for event_date in dates:
        structured_data = current_app.json.dumps(
            get_sd_for_event_date(event_date, event), indent=2
        )
        structured_datas.append(structured_data)

    definition = event.min_start_definition

    return render_template(
        "event/shell.html",
        entry="public",
        title=event.name,
        boot=build_boot_data(base="/"),
        event=event,
        start=definition.start,
        end=definition.end,
        allday=definition.allday,
        structured_datas=structured_datas,
        meta=get_meta_data(event),
        canonical_url=url_for("main.event", event_id=event_id, _external=True),
    )


@main_bp.route("/event/<int:event_id>/actions")
@inject
def event_actions(event_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))

    return render_template(
        "layout_vue3.html",
        entry="public",
        title=gettext("Actions for event"),
        boot=build_boot_data(base="/"),
    )


@main_bp.route("/event/<int:event_id>/report")
@inject
def event_report(event_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))

    return render_template(
        "layout_vue3.html",
        entry="public",
        title=gettext("Report event"),
        boot=build_boot_data(base="/"),
    )


@main_bp.route("/event/<int:id>/ical")
@inject
def event_ical(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=id)))

    ical_events = create_ical_events_for_event(event)

    cal = create_icalendar()
    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=event_{id}.ics"},
    )
