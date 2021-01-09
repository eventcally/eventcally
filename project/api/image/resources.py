from project import rest_api, api_docs
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.image.schemas import ImageSchema
from project.models import AdminUnit


class ImageResource(MethodResource):
    @doc(tags=["Images"])
    @marshal_with(ImageSchema)
    def get(self, id):
        return AdminUnit.query.get_or_404(id)


rest_api.add_resource(ImageResource, "/images/<int:id>")
api_docs.register(ImageResource)
