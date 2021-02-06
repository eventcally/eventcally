from project.api import add_api_resource
from flask import make_response
from flask_apispec import marshal_with, doc, use_kwargs
from project.api.resources import BaseResource
from project.api.place.schemas import (
    PlaceSchema,
    PlacePostRequestSchema,
    PlacePatchRequestSchema,
)
from project.models import EventPlace
from project.oauth2 import require_oauth
from authlib.integrations.flask_oauth2 import current_token
from project import db
from project.access import access_or_401, login_api_user_or_401


class PlaceResource(BaseResource):
    @doc(summary="Get place", tags=["Places"])
    @marshal_with(PlaceSchema)
    def get(self, id):
        return EventPlace.query.get_or_404(id)

    @doc(
        summary="Update place", tags=["Places"], security=[{"oauth2": ["place:write"]}]
    )
    @use_kwargs(PlacePostRequestSchema, location="json")
    @marshal_with(None, 204)
    @require_oauth("place:write")
    def put(self, id, **kwargs):
        login_api_user_or_401(current_token.user)
        place = EventPlace.query.get_or_404(id)
        access_or_401(place.adminunit, "place:update")

        place = PlacePostRequestSchema(load_instance=True).load(
            kwargs, session=db.session, instance=place
        )
        db.session.commit()

        return make_response("", 204)

    @doc(summary="Patch place", tags=["Places"], security=[{"oauth2": ["place:write"]}])
    @use_kwargs(PlacePatchRequestSchema, location="json")
    @marshal_with(None, 204)
    @require_oauth("place:write")
    def patch(self, id, **kwargs):
        login_api_user_or_401(current_token.user)
        place = EventPlace.query.get_or_404(id)
        access_or_401(place.adminunit, "place:update")

        place = PlacePatchRequestSchema(load_instance=True).load(
            kwargs, session=db.session, instance=place
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete place", tags=["Places"], security=[{"oauth2": ["place:write"]}]
    )
    @marshal_with(None, 204)
    @require_oauth("place:write")
    def delete(self, id):
        login_api_user_or_401(current_token.user)
        place = EventPlace.query.get_or_404(id)
        access_or_401(place.adminunit, "place:delete")

        db.session.delete(place)
        db.session.commit()

        return make_response("", 204)


add_api_resource(PlaceResource, "/places/<int:id>", "api_v1_place")
