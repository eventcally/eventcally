from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project import db
from project.access import access_or_401, login_api_user_or_401
from project.api import add_api_resource
from project.api.place.schemas import (
    PlacePatchRequestSchema,
    PlacePostRequestSchema,
    PlaceSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import EventPlace


class PlaceResource(BaseResource):
    @doc(summary="Get place", tags=["Places"])
    @marshal_with(PlaceSchema)
    @require_api_access()
    def get(self, id):
        return EventPlace.query.get_or_404(id)

    @doc(
        summary="Update place",
        tags=["Places"],
    )
    @use_kwargs(PlacePostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("place:write")
    def put(self, id):
        login_api_user_or_401()
        place = EventPlace.query.get_or_404(id)
        access_or_401(place.adminunit, "event_places:write")

        place = self.update_instance(PlacePostRequestSchema, instance=place)
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch place",
        tags=["Places"],
    )
    @use_kwargs(PlacePatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("place:write")
    def patch(self, id):
        login_api_user_or_401()
        place = EventPlace.query.get_or_404(id)
        access_or_401(place.adminunit, "event_places:write")

        place = self.update_instance(PlacePatchRequestSchema, instance=place)
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete place",
        tags=["Places"],
    )
    @marshal_with(None, 204)
    @require_api_access("place:write")
    def delete(self, id):
        login_api_user_or_401()
        place = EventPlace.query.get_or_404(id)
        access_or_401(place.adminunit, "event_places:write")

        db.session.delete(place)
        db.session.commit()

        return make_response("", 204)


add_api_resource(PlaceResource, "/places/<int:id>", "api_v1_place")
