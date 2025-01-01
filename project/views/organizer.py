from flask import Response, render_template

from project import app
from project.dateutils import create_icalendar
from project.models import EventOrganizer
from project.services.organizer import create_ical_events_for_organizer


@app.route("/organizers")
@app.route("/organizers/<path:path>")
def organizers(path=None):
    return render_template("organizer/main.html")


@app.route("/organizers/<int:id>/ical")
def organizer_ical(id):
    organizer = EventOrganizer.query.get_or_404(id)

    cal = create_icalendar()
    cal.add("x-wr-calname", organizer.name)
    ical_events = create_ical_events_for_organizer(organizer)

    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=organizer_{id}.ics"},
    )
