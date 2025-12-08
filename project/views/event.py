from datetime import datetime

from flask import Response, jsonify, render_template, request, url_for
from flask_security import current_user

from project import app
from project.access import (
    can_read_event_or_401,
    can_reference_event,
    can_request_event_reference,
    get_admin_unit_members_with_permission,
    has_access,
)
from project.dateutils import create_icalendar
from project.jsonld import get_sd_for_event_date
from project.models import Event, EventCategory
from project.services.event import (
    create_ical_events_for_event,
    get_event_with_details_or_404,
    get_meta_data,
    get_upcoming_event_dates,
)
from project.utils import get_event_category_name
from project.views.utils import (
    get_calendar_links_for_event,
    get_share_links,
    send_template_mails_to_users_async,
)


@app.route("/event/<int:event_id>")
def event(event_id):
    event = get_event_with_details_or_404(event_id)
    can_read_event_or_401(event)
    user_rights = get_user_rights(event)
    dates = get_upcoming_event_dates(event.id)
    url = url_for("event", event_id=event_id, _external=True)
    share_links = get_share_links(url, event.name)
    calendar_links = get_calendar_links_for_event(event)

    structured_datas = list()
    for event_date in dates:
        structured_data = app.json.dumps(get_sd_for_event_date(event_date), indent=2)
        structured_datas.append(structured_data)

    return render_template(
        "event/read.html",
        event=event,
        dates=dates,
        structured_datas=structured_datas,
        meta=get_meta_data(event),
        user_rights=user_rights,
        canonical_url=url_for("event", event_id=event_id, _external=True),
        share_links=share_links,
        calendar_links=calendar_links,
    )


@app.route("/event/<int:event_id>/actions")
def event_actions(event_id):
    event = Event.query.get_or_404(event_id)
    can_read_event_or_401(event)
    user_rights = get_user_rights(event)
    url = url_for("event", event_id=event_id, _external=True)
    share_links = get_share_links(url, event.name)

    return render_template(
        "event/actions.html",
        event=event,
        user_rights=user_rights,
        share_links=share_links,
    )


@app.route("/event/<int:event_id>/report")
def event_report(event_id):
    event = Event.query.get_or_404(event_id)
    can_read_event_or_401(event)

    return render_template("event/report.html")


@app.route("/events/rrule", methods=["POST"])
def event_rrule():
    year = request.json["year"]
    month = request.json["month"]
    day = request.json["day"]
    rrule_str = request.json["rrule"]
    start = int(request.json["start"])
    batch_size = 10
    start_date = datetime(year, month, day)

    from project.dateutils import calculate_occurrences

    try:
        result = calculate_occurrences(
            start_date, '"%d.%m.%Y"', rrule_str, start, batch_size
        )
        return jsonify(result)
    except Exception as e:
        app.logger.exception(request.json)
        return getattr(e, "message", "Unknown error"), 400


def get_event_category_choices():
    return sorted(
        [(c.id, get_event_category_name(c)) for c in EventCategory.query.all()],
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


def send_event_report_mails(event: Event, report: dict):
    from project.services.user import find_all_users_with_role

    # Alle Mitglieder der AdminUnit, die das Recht haben, Events zu bearbeiten
    members = get_admin_unit_members_with_permission(
        event.admin_unit_id, "events:write"
    )
    users = [member.user for member in members]

    # Alle globalen Admins
    admins = find_all_users_with_role("admin")
    users.extend(
        admin for admin in admins if all(user.id != admin.id for user in users)
    )

    send_template_mails_to_users_async(
        users,
        "event_report_notice",
        event=event,
        report=report,
    )


@app.route("/event/<int:id>/ical")
def event_ical(id):
    event = get_event_with_details_or_404(id)
    can_read_event_or_401(event)

    ical_events = create_ical_events_for_event(event)

    cal = create_icalendar()
    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=event_{id}.ics"},
    )
