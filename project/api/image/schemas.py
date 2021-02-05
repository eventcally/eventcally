from project.api import marshmallow
from project.models import Image


class ImageIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Image

    id = marshmallow.auto_field()


class ImageBaseSchema(ImageIdSchema):
    copyright_text = marshmallow.auto_field()


class ImageSchema(ImageBaseSchema):
    image_url = marshmallow.URLFor(
        "image",
        values=dict(id="<id>", s=500),
        metadata={
            "description": "Append query arguments w for width, h for height or s for size(width and height)."
        },
    )


class ImageDumpSchema(ImageBaseSchema):
    pass
