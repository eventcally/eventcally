from project import app
from project.models import EventDate, Event, AdminUnit
from project.dateutils import today
from flask import jsonify
from project.jsonld import get_sd_for_event_date
from project.services.event import get_event_dates_query
from project.services.event_search import EventSearchParams
from project.services.organizer import get_event_places

@app.route("/api/events")
def api_events():
    dates = EventDate.query.join(Event).filter(EventDate.start >= today).order_by(EventDate.start).all()
    return json_from_event_dates(dates)

@app.route("/api/event_dates")
def api_event_dates():
    params = EventSearchParams()
    params.load_from_request()

    dates = get_event_dates_query(params).paginate()
    return json_from_event_dates(dates.items)

@app.route("/api/<string:au_short_name>/event_dates")
def api_infoscreen(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()

    params = EventSearchParams()
    params.load_from_request()
    params.admin_unit_id = admin_unit.id

    dates = get_event_dates_query(params).paginate()
    return json_from_event_dates(dates.items)

@app.route("/api/organizer/<int:id>/event_places")
def api_event_places(id):
    places = get_event_places(id)
    result = list()

    for place in places:
        item = {}
        item["id"] = place.id
        item["name"] = place.name
        result.append(item)

    return jsonify(result)

def json_from_event_dates(dates):
    structured_events = list()
    for event_date in dates:
        structured_event = get_sd_for_event_date(event_date)
        structured_event.pop('@context', None)
        structured_events.append(structured_event)

    result = {}
    result["@context"] = "https://schema.org"
    result["@type"] = "Project"
    result["name"] = "Prototyp"
    result['event'] = structured_events
    return jsonify(result)