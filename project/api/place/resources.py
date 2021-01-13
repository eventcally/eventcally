from project import rest_api, api_docs
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.place.schemas import PlaceSchema
from project.models import EventPlace


class PlaceResource(MethodResource):
    @doc(tags=["Places"])
    @marshal_with(PlaceSchema)
    def get(self, id):
        return EventPlace.query.get_or_404(id)


rest_api.add_resource(
    PlaceResource,
    "/places/<int:id>",
)
api_docs.register(PlaceResource)