from project.api import add_api_resource
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.place.schemas import PlaceSchema
from project.models import EventPlace


class PlaceResource(MethodResource):
    @doc(summary="Get place", tags=["Places"])
    @marshal_with(PlaceSchema)
    def get(self, id):
        return EventPlace.query.get_or_404(id)


add_api_resource(PlaceResource, "/places/<int:id>", "api_v1_place")
