from flask import abort

from project.infrastructure.extensions import limiter
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import (
    PlaceCoordinate,
    PlaceSuggestion,
    PlaceSuggestionList,
    PlaceSuggestionParams,
)
from project.presentation.shared.maputils import find_gmaps_places, get_gmaps_place

# Both routes call Google, so anonymous visitors share one limit.
PLACE_SUGGESTION_RATE_LIMIT = "30/minute;300/hour"
PLACE_SUGGESTION_RATE_LIMIT_SCOPE = "bff_public_places"


@bff_route(
    bff_public_bp,
    "/places",
    query=PlaceSuggestionParams,
    response=PlaceSuggestionList,
    summary="Suggest places (Google Maps) for a location filter",
)
def list_place_suggestions(query: PlaceSuggestionParams):
    with limiter.shared_limit(
        PLACE_SUGGESTION_RATE_LIMIT, scope=PLACE_SUGGESTION_RATE_LIMIT_SCOPE
    ):
        if not query.keyword.strip():
            return PlaceSuggestionList(items=[])

        places = find_gmaps_places(query.keyword)

    return PlaceSuggestionList(
        items=[
            PlaceSuggestion(
                gmaps_id=p["place_id"],
                text=p["description"],
                main_text=p.get("structured_formatting", {}).get("main_text"),
            )
            for p in places
        ]
    )


@bff_route(
    bff_public_bp,
    "/places/<gmaps_id>/coordinate",
    response=PlaceCoordinate,
    summary="The coordinate of a Google Maps place",
)
def get_place_coordinate(gmaps_id: str):
    with limiter.shared_limit(
        PLACE_SUGGESTION_RATE_LIMIT, scope=PLACE_SUGGESTION_RATE_LIMIT_SCOPE
    ):
        place = get_gmaps_place(gmaps_id)

    location = (place or {}).get("geometry", {}).get("location")

    if not location:
        abort(404)

    return PlaceCoordinate(latitude=location["lat"], longitude=location["lng"])
