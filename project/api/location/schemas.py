from marshmallow import fields, validate
from project.api import marshmallow
from project.models import Location
from project.api.fields import NumericStr


class LocationIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Location


class LocationSchema(LocationIdSchema):
    street = marshmallow.auto_field()
    postalCode = marshmallow.auto_field()
    city = marshmallow.auto_field()
    state = marshmallow.auto_field()
    country = marshmallow.auto_field()
    longitude = NumericStr()
    latitude = NumericStr()


class LocationDumpSchema(LocationSchema):
    pass


class LocationSearchItemSchema(LocationSchema):
    pass


class LocationPostRequestSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Location

    street = fields.Str(validate=validate.Length(max=255), missing=None)
    postalCode = fields.Str(validate=validate.Length(max=10), missing=None)
    city = fields.Str(validate=validate.Length(max=255), missing=None)
    state = fields.Str(validate=validate.Length(max=255), missing=None)
    country = fields.Str(validate=validate.Length(max=255), missing=None)
    longitude = NumericStr(validate=validate.Range(-180, 180), missing=None)
    latitude = NumericStr(validate=validate.Range(-90, 90), missing=None)


class LocationPostRequestLoadSchema(LocationPostRequestSchema):
    class Meta:
        model = Location
        load_instance = True


class LocationPatchRequestSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Location

    street = fields.Str(validate=validate.Length(max=255), allow_none=True)
    postalCode = fields.Str(validate=validate.Length(max=10), allow_none=True)
    city = fields.Str(validate=validate.Length(max=255), allow_none=True)
    state = fields.Str(validate=validate.Length(max=255), allow_none=True)
    country = fields.Str(validate=validate.Length(max=255), allow_none=True)
    longitude = NumericStr(validate=validate.Range(-180, 180), allow_none=True)
    latitude = NumericStr(validate=validate.Range(-90, 90), allow_none=True)


class LocationPatchRequestLoadSchema(LocationPatchRequestSchema):
    class Meta:
        model = Location
        load_instance = True
