from project import marshmallow
from project.models import Image


class ImageSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Image

    id = marshmallow.auto_field()
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()
    image_url = marshmallow.URLFor("image", values=dict(id="<id>"))
    copyright_text = marshmallow.auto_field()


class ImageRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Image

    id = marshmallow.auto_field()
    image_url = marshmallow.URLFor("image", values=dict(id="<id>"))
    href = marshmallow.URLFor(
        "imageresource",
        values=dict(id="<id>"),
    )
