from project.api import add_api_resource
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.location.schemas import LocationSchema
from project.models import Location


class LocationResource(MethodResource):
    @doc(summary="Get location", tags=["Locations"])
    @marshal_with(LocationSchema)
    def get(self, id):
        return Location.query.get_or_404(id)


add_api_resource(LocationResource, "/locations/<int:id>", "api_v1_location")
