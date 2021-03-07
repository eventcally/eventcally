from flask import jsonify

from project import app
from project.dateutils import get_today
from project.jsonld import get_sd_for_event_date
from project.models import Event, EventDate
from project.services.event import get_event_dates_query
from project.services.event_search import EventSearchParams


@app.route("/api/events")
def api_events():
    today = today = get_today()
    dates = (
        EventDate.query.join(Event)
        .filter(EventDate.start >= today)
        .order_by(EventDate.start)
        .all()
    )
    return json_from_event_dates(dates)


@app.route("/api/event_dates")
def api_event_dates():
    params = EventSearchParams()
    params.load_from_request()

    dates = get_event_dates_query(params).paginate()
    return json_from_event_dates(dates.items)


def json_from_event_dates(dates):
    structured_events = list()
    for event_date in dates:
        structured_event = get_sd_for_event_date(event_date)
        structured_event.pop("@context", None)
        structured_events.append(structured_event)

    result = {}
    result["@context"] = "https://schema.org"
    result["@type"] = "Project"
    result["name"] = "Prototyp"
    result["event"] = structured_events
    return jsonify(result)
