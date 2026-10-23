from flask import abort

from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import (
    PlaceCoordinate,
    PlaceSuggestion,
    PlaceSuggestionList,
    PlaceSuggestionParams,
)
from project.presentation.shared.access import can_use_manage_place_lookup
from project.presentation.shared.maputils import find_gmaps_places, get_gmaps_place


@bff_route(
    bff_manage_bp,
    "/places",
    query=PlaceSuggestionParams,
    response=PlaceSuggestionList,
    summary="Suggest places (Google Maps) for a location filter",
)
def list_place_suggestions(query: PlaceSuggestionParams):
    if not can_use_manage_place_lookup():
        raise UnauthorizedError()

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
    bff_manage_bp,
    "/places/<gmaps_id>/coordinate",
    response=PlaceCoordinate,
    summary="The coordinate of a Google Maps place",
)
def get_place_coordinate(gmaps_id: str):
    if not can_use_manage_place_lookup():
        raise UnauthorizedError()

    place = get_gmaps_place(gmaps_id)
    location = (place or {}).get("geometry", {}).get("location")

    if not location:
        abort(404)

    return PlaceCoordinate(latitude=location["lat"], longitude=location["lng"])
