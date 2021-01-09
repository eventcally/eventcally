from project import marshmallow
from project.models import Image


class ImageSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Image

    id = marshmallow.auto_field()
    copyright_text = marshmallow.auto_field()
    image_url = marshmallow.URLFor("image", values=dict(id="<id>"))


class ImageRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Image

    id = marshmallow.auto_field()
    copyright_text = marshmallow.auto_field()
    image_url = marshmallow.URLFor("image", values=dict(id="<id>"))
    href = marshmallow.URLFor(
        "imageresource",
        values=dict(id="<id>"),
    )
