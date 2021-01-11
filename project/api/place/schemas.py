from marshmallow import fields
from project import marshmallow
from project.models import EventPlace
from project.api.image.schemas import ImageRefSchema
from project.api.location.schemas import LocationRefSchema
from project.api.organization.schemas import OrganizationRefSchema


class PlaceSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    location = fields.Nested(LocationRefSchema)
    photo = fields.Nested(ImageRefSchema)
    url = marshmallow.auto_field()
    description = marshmallow.auto_field()
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class PlaceRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    href = marshmallow.URLFor(
        "placeresource",
        values=dict(id="<id>"),
    )
