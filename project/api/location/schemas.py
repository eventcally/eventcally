from marshmallow import fields
from project import marshmallow
from project.models import Location


class LocationIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Location

    id = marshmallow.auto_field()


class LocationSchema(LocationIdSchema):
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()
    street = marshmallow.auto_field()
    postalCode = marshmallow.auto_field()
    city = marshmallow.auto_field()
    state = marshmallow.auto_field()
    country = marshmallow.auto_field()
    longitude = fields.Str()
    latitude = fields.Str()


class LocationDumpSchema(LocationSchema):
    pass


class LocationRefSchema(LocationIdSchema):
    pass


class LocationSearchItemSchema(LocationRefSchema):
    class Meta:
        model = Location

    longitude = fields.Str()
    latitude = fields.Str()
