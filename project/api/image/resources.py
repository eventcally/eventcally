from project.api import add_api_resource
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.image.schemas import ImageSchema
from project.models import Image


class ImageResource(MethodResource):
    @doc(summary="Get image", tags=["Images"])
    @marshal_with(ImageSchema)
    def get(self, id):
        return Image.query.get_or_404(id)


add_api_resource(ImageResource, "/images/<int:id>", "api_v1_image")
