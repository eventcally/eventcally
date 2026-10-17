from dateutil.relativedelta import relativedelta
from dependency_injector.wiring import Provide, inject
from flask import Response, render_template

from project.api.event.query_args import event_search_criteria_from_request
from project.application.queries import GetOrganizationQuery, ListAllEventsQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.dateutils import create_icalendar, get_today
from project.ical import create_ical_events_for_events
from project.views.main_blueprint import main_bp
from project.views.utils import result_or_404


@main_bp.route("/organizations")
@main_bp.route("/organizations/")
@main_bp.route("/organizations/<path:path>")
def organizations(path=None):
    return render_template("organization/main.html")


@main_bp.route("/organizations/<int:id>/ical")
@inject
def organization_ical(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    admin_unit = result_or_404(query_bus.handle(GetOrganizationQuery(id=id)))

    cal = create_icalendar()
    cal.add("x-wr-calname", admin_unit.name)
    events = query_bus.handle(
        ListAllEventsQuery(
            criteria=event_search_criteria_from_request(
                {},
                defaults=dict(include_admin_unit_references=True),
                date_from=get_today() - relativedelta(months=1),
                admin_unit_id=admin_unit.id,
            )
        )
    )
    ical_events = create_ical_events_for_events(events)

    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=organization_{id}.ics"},
    )
