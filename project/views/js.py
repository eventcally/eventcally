import json
from datetime import datetime

import icalendar
import recurring_ical_events
import requests
from flask import request
from flask.json import jsonify
from flask_babel import gettext
from flask_cors import cross_origin
from flask_security import auth_required, url_for_security
from flask_security.utils import localize_callback
from sqlalchemy import func

from project import app, csrf
from project.api.custom_widget.schemas import CustomWidgetSchema
from project.dateutils import form_input_to_date
from project.maputils import find_gmaps_places, get_gmaps_place
from project.models import AdminUnit, CustomWidget, EventOrganizer, EventPlace
from project.services.admin import upsert_settings
from project.services.place import get_event_places
from project.services.user import find_user_by_email
from project.utils import decode_response_content, get_place_str


@app.route("/js/check/organization/short_name", methods=["POST"])
def js_check_org_short_name():
    csrf.protect()

    short_name = request.form["short_name"]
    admin_unit_id = (
        int(request.form["admin_unit_id"]) if "admin_unit_id" in request.form else -1
    )
    organization = AdminUnit.query.filter(
        func.lower(AdminUnit.short_name) == short_name.lower()
    ).first()

    if not organization or organization.id == admin_unit_id:
        return jsonify(True)

    error = gettext("Short name is already taken")
    return jsonify(error)


@app.route("/js/check/organization/name", methods=["POST"])
def js_check_org_name():
    csrf.protect()

    name = request.form["name"]
    admin_unit_id = (
        int(request.form["admin_unit_id"]) if "admin_unit_id" in request.form else -1
    )
    organization = AdminUnit.query.filter(
        func.lower(AdminUnit.name) == name.lower()
    ).first()

    if not organization or organization.id == admin_unit_id:
        return jsonify(True)

    error = gettext("Name is already taken")
    return jsonify(error)


@app.route("/js/check/event_place/name", methods=["POST"])
def js_check_event_place_name():
    csrf.protect()

    name = request.form["name"]
    admin_unit_id = (
        int(request.form["admin_unit_id"]) if "admin_unit_id" in request.form else -1
    )
    event_place_id = (
        int(request.form["event_place_id"]) if "event_place_id" in request.form else -1
    )
    event_place = (
        EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)
        .filter(func.lower(EventPlace.name) == name.lower())
        .first()
    )

    if not event_place or event_place.id == event_place_id:
        return jsonify(True)

    error = gettext("A place already exists with this name.")
    return jsonify(error)


@app.route("/js/check/organizer/name", methods=["POST"])
def js_check_organizer_name():
    csrf.protect()

    name = request.form["name"]
    admin_unit_id = (
        int(request.form["admin_unit_id"]) if "admin_unit_id" in request.form else -1
    )
    organizer_id = (
        int(request.form["organizer_id"]) if "organizer_id" in request.form else -1
    )
    organizer = (
        EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit_id)
        .filter(func.lower(EventOrganizer.name) == name.lower())
        .first()
    )

    if not organizer or organizer.id == organizer_id:
        return jsonify(True)

    error = gettext("An organizer already exists with this name.")
    return jsonify(error)


@app.route("/js/check/register/email", methods=["POST"])
def js_check_register_email():
    csrf.protect()

    email = request.form["email"]
    user = find_user_by_email(email)

    if not user:
        return jsonify(True)

    msg = gettext("An account already exists with this email.")
    url = url_for_security("forgot_password")
    link_text = localize_callback("Forgot password")
    link = ' &ndash; <a href="%s">%s</a>' % (url, link_text)
    error = msg + link
    return jsonify(error)


@app.route("/js/autocomplete/place")
def js_autocomplete_place():
    csrf.protect()

    admin_unit_id = int(request.args.get("admin_unit_id", "0"))
    keyword = request.args.get("keyword")
    exclude_gmaps = request.args.get("exclude_gmaps")
    places_result = list()
    google_places_result = list()

    if admin_unit_id > 0:
        places = get_event_places(admin_unit_id, keyword, 5)
        places_result = [{"id": p.id, "text": get_place_str(p)} for p in places]

    if not exclude_gmaps:
        google_places = find_gmaps_places(keyword) if keyword else list()
        google_places_result = [
            {
                "id": p["place_id"],
                "gmaps_id": p["place_id"],
                "text": p["description"],
                "main_text": p["structured_formatting"]["main_text"],
            }
            for p in google_places
        ]

    if exclude_gmaps:
        results = places_result
    elif admin_unit_id <= 0:
        results = google_places_result
    else:
        results = list()

        if len(places) > 0:
            results.append(
                {
                    "text": gettext("Places of organization"),
                    "children": places_result,
                }
            )

        if len(google_places) > 0:
            results.append(
                {
                    "text": gettext("Places of Google Maps"),
                    "children": google_places_result,
                }
            )

    result = {"results": results}
    return jsonify(result)


@app.route("/js/autocomplete/gmaps_place")
def js_autocomplete_gmaps_place():
    csrf.protect()

    gmaps_id = request.args["gmaps_id"]
    place = get_gmaps_place(gmaps_id)
    return jsonify(place)


@app.route("/js/icalevents", methods=["POST"])
@auth_required()
def js_icalevents():
    csrf.protect()

    try:
        url = request.form["url"]
        date_from = request.form["date_from"]
        date_to = request.form["date_to"]

        start_date = form_input_to_date(date_from).date()
        end_date = form_input_to_date(date_to).date()

        settings = upsert_settings()
        planning_external_calendars_str = (
            settings.planning_external_calendars
            if settings.planning_external_calendars
            else "[]"
        )
        external_calendars = json.loads(planning_external_calendars_str)
        external_calendar = next((c for c in external_calendars if c["url"] == url))

        response = requests.get(external_calendar["url"])
        ical_string = decode_response_content(response)
        calendar = icalendar.Calendar.from_ical(ical_string)
        events = recurring_ical_events.of(calendar).between(start_date, end_date)
        items = list()

        for event in events:
            summary = event.get("SUMMARY")
            dt_start = event.get("DTSTART")
            dt_end = event.get("DTEND")
            location = event.get("LOCATION")
            description = event.get("DESCRIPTION")

            if not summary or not dt_start:  # pragma: no cover
                continue

            start = dt_start.dt

            item = {
                "name": summary,
                "start": start,
                "allday": not isinstance(start, datetime),
            }

            if dt_end:
                item["end"] = dt_end.dt

            vevent = {
                "url": url,
            }

            if location:
                vevent["location"] = location

            if dt_end:
                vevent["description"] = description

            item["vevent"] = vevent
            items.append(item)

        result = {
            "url": url,
            "items": items,
        }

        return jsonify(result)
    except Exception as e:  # pragma: no cover
        app.logger.exception(url)
        return getattr(e, "message", "Unknown error"), 400


@app.route("/js/wlcw/<int:id>")
@cross_origin()
def js_widget_loader_custom_widget(id: int):
    widget = CustomWidget.query.get_or_404(id)
    schema = CustomWidgetSchema()
    return schema.dump(widget)
