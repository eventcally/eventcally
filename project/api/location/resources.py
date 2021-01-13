from project import rest_api, api_docs
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.location.schemas import LocationSchema
from project.models import Location


class LocationResource(MethodResource):
    @doc(tags=["Locations"])
    @marshal_with(LocationSchema)
    def get(self, id):
        return Location.query.get_or_404(id)


rest_api.add_resource(LocationResource, "/locations/<int:id>")
api_docs.register(LocationResource)
