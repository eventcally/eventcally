from flask import request
from flask.json import jsonify
from flask_babelex import gettext

from project import app, csrf
from project.maputils import find_gmaps_places, get_gmaps_place
from project.models import AdminUnit
from project.services.place import get_event_places
from project.services.user import find_user_by_email
from project.utils import get_place_str


@app.route("/js/check/organization/short_name", methods=["POST"])
def js_check_org_short_name():
    csrf.protect()

    short_name = request.form["short_name"]
    admin_unit_id = (
        int(request.form["admin_unit_id"]) if "admin_unit_id" in request.form else -1
    )
    organization = AdminUnit.query.filter(AdminUnit.short_name == short_name).first()

    if not organization or organization.id == admin_unit_id:
        return jsonify(True)

    error = gettext("Short name is already taken")
    return jsonify(error)


@app.route("/js/check/register/email", methods=["POST"])
def js_check_register_email():
    csrf.protect()

    email = request.form["email"]
    user = find_user_by_email(email)

    if not user:
        return jsonify(True)

    error = gettext("An account already exists with this email.")
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
