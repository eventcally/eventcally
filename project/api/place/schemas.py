from marshmallow import fields
from project import marshmallow
from project.models import EventPlace
from project.api.image.schemas import ImageRefSchema
from project.api.location.schemas import LocationRefSchema


class PlaceSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    description = marshmallow.auto_field()
    photo = fields.Nested(ImageRefSchema)
    location = fields.Nested(LocationRefSchema)


class PlaceRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    href = marshmallow.URLFor(
        "placeresource",
        values=dict(id="<id>"),
    )
    location = fields.Nested(LocationRefSchema)
