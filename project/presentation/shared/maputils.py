import logging

import googlemaps
from flask import current_app

google_maps_api_key = None
gmaps = None


logger = logging.getLogger(__name__)


def _init_gmaps():
    """Lazy initialization of Google Maps client."""
    global google_maps_api_key, gmaps
    if google_maps_api_key is None:
        google_maps_api_key = current_app.config["GOOGLE_MAPS_API_KEY"]
        gmaps = (
            googlemaps.Client(key=google_maps_api_key) if google_maps_api_key else None
        )


def find_gmaps_places(query: str) -> list:
    _init_gmaps()
    result = list()

    if gmaps:
        try:
            places = gmaps.places_autocomplete_query(
                query, location=(51.9059531, 10.4289963), radius=1000000, language="de"
            )
            result = list(filter(lambda p: "place_id" in p, places))

        except Exception:  # pragma: no cover
            logger.exception("Google Maps place search failed")

    return result


def get_gmaps_place(gmaps_id) -> dict:
    _init_gmaps()
    result = dict()

    if gmaps:
        try:
            place = gmaps.place(
                gmaps_id,
                fields=["address_component", "geometry", "name"],
                language="de",
            )

            if place["status"] == "OK":
                result = place["result"]
        except Exception:  # pragma: no cover
            logger.exception(
                "Google Maps place lookup failed", extra={"gmaps_id": gmaps_id}
            )

    return result


def get_gmaps_place_address(place: dict) -> dict:
    """Maps the address components of a Google place to location fields."""
    street_number = ""
    route = ""
    address = dict(city="", state="", postalCode="")

    for component in place.get("address_components", []):
        address_type = component["types"][0]
        value = component["long_name"]

        if address_type == "street_number":
            street_number = value
        elif address_type == "route":
            route = value
        elif address_type == "locality":
            address["city"] = value
        elif address_type == "administrative_area_level_1":
            address["state"] = value
        elif address_type == "postal_code":
            address["postalCode"] = value

    location = place["geometry"]["location"]
    address["street"] = " ".join([route, street_number]).strip()
    address["latitude"] = location["lat"]
    address["longitude"] = location["lng"]
    return address
