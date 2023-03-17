import googlemaps

from project import app

google_maps_api_key = app.config["GOOGLE_MAPS_API_KEY"]
gmaps = googlemaps.Client(key=google_maps_api_key) if google_maps_api_key else None


def find_gmaps_places(query: str) -> list:
    result = list()

    if gmaps:
        try:
            places = gmaps.places_autocomplete_query(
                query, location=(51.9059531, 10.4289963), radius=1000000, language="de"
            )
            result = list(filter(lambda p: "place_id" in p, places))

        except Exception as e:  # pragma: no cover
            app.logger.exception(e)

    return result


def get_gmaps_place(gmaps_id) -> dict:
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
        except Exception as e:  # pragma: no cover
            app.logger.exception(e)

    return result
