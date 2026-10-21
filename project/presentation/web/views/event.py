from datetime import datetime

from dependency_injector.wiring import Provide, inject
from flask import Response, current_app, jsonify, render_template, request, url_for
from flask_babel import gettext
from flask_security import current_user

from project.application.queries import (
    GetEventDetailQuery,
    ListAllEventCategoriesQuery,
    ListUpcomingEventDatesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.access import (
    can_reference_event,
    can_request_event_reference,
    has_access,
)
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.ical import create_ical_events_for_event
from project.presentation.web.jsonld import get_sd_for_event_date
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import (
    get_calendar_links_for_event,
    get_meta_data,
    get_share_links,
)
from project.shared.dateutils import create_icalendar
from project.shared.utils import get_event_category_name


@main_bp.route("/event/<int:event_id>")
@inject
def event(event_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))
    user_rights = get_user_rights(event)
    dates = query_bus.handle(ListUpcomingEventDatesQuery(event_id=event.id))
    url = url_for("main.event", event_id=event_id, _external=True)
    share_links = get_share_links(url, event.name)
    calendar_links = get_calendar_links_for_event(event)

    structured_datas = list()
    for event_date in dates:
        structured_data = current_app.json.dumps(
            get_sd_for_event_date(event_date, event), indent=2
        )
        structured_datas.append(structured_data)

    return render_template(
        "event/read.html",
        event=event,
        dates=dates,
        structured_datas=structured_datas,
        meta=get_meta_data(event),
        user_rights=user_rights,
        canonical_url=url_for("main.event", event_id=event_id, _external=True),
        share_links=share_links,
        calendar_links=calendar_links,
    )


@main_bp.route("/event/<int:event_id>/actions")
@inject
def event_actions(event_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))
    user_rights = get_user_rights(event)
    url = url_for("main.event", event_id=event_id, _external=True)
    share_links = get_share_links(url, event.name)

    return render_template(
        "event/actions.html",
        event=event,
        user_rights=user_rights,
        share_links=share_links,
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


@main_bp.route("/events/rrule", methods=["POST"])
def event_rrule():
    year = request.json["year"]
    month = request.json["month"]
    day = request.json["day"]
    rrule_str = request.json["rrule"]
    start = int(request.json["start"])
    batch_size = 10
    start_date = datetime(year, month, day)

    from project.shared.dateutils import calculate_occurrences

    try:
        result = calculate_occurrences(
            start_date, '"%d.%m.%Y"', rrule_str, start, batch_size
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(request.json)
        return getattr(e, "message", "Unknown error"), 400


def get_event_category_choices():
    categories = current_app.container.cqrs.query_bus().handle(
        ListAllEventCategoriesQuery()
    )
    return sorted(
        [(c.id, get_event_category_name(c)) for c in categories],
        key=lambda category: category[1],
    )


def get_user_rights(event):
    return {
        "can_duplicate_event": has_access(event.admin_unit, "events:write"),
        "can_verify_event": has_access(event.admin_unit, "event:verify"),
        "can_reference_event": can_reference_event(event),
        "can_create_reference_request": can_request_event_reference(event),
        "can_create_event": has_access(event.admin_unit, "events:write"),
        "can_view_actions": current_user.is_authenticated,
        "can_update_event": has_access(event.admin_unit, "events:write"),
    }


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
