from marshmallow import fields
from project import marshmallow
from project.models import Location


class LocationSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Location

    id = marshmallow.auto_field()
    street = marshmallow.auto_field()
    postalCode = marshmallow.auto_field()
    city = marshmallow.auto_field()
    state = marshmallow.auto_field()
    country = marshmallow.auto_field()
    longitude = fields.Str()
    latitude = fields.Str()


class LocationRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Location

    id = marshmallow.auto_field()
    href = marshmallow.URLFor(
        "locationresource",
        values=dict(id="<id>"),
    )
