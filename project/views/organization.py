from flask import Response, render_template

from project import app
from project.dateutils import create_icalendar
from project.models import AdminUnit
from project.services.admin_unit import create_ical_events_for_admin_unit


@app.route("/organizations")
@app.route("/organizations/<path:path>")
def organizations(path=None):
    return render_template("organization/main.html")


@app.route("/organizations/<int:id>/ical")
def organization_ical(id):
    admin_unit = AdminUnit.query.get_or_404(id)

    cal = create_icalendar()
    cal.add("x-wr-calname", admin_unit.name)
    ical_events = create_ical_events_for_admin_unit(admin_unit)

    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=organization_{id}.ics"},
    )
