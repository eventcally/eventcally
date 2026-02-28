from marshmallow import ValidationError, fields, post_load, validate, validates_schema

from project.api.fields import NumericStr
from project.api.schemas import PlainBaseSchema, SQLAlchemyBaseSchema
from project.domain.commands import CreateLocation, UpdateLocation
from project.domain.types import unset
from project.models import Location


class LocationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = Location
        load_instance = True


class LocationCoordinateValidationMixin:
    @validates_schema
    def validate_location(self, data, **kwargs):
        lat_set = "latitude" in data and data["latitude"] is not None
        lon_set = "longitude" in data and data["longitude"] is not None

        if lat_set and not lon_set:
            raise ValidationError("If latitude is given, longitude is required.")

        if lon_set and not lat_set:
            raise ValidationError("If longitude is given, latitude is required.")


class LocationBaseSchemaMixin(LocationCoordinateValidationMixin):
    street = fields.Str(validate=validate.Length(max=255))
    postalCode = fields.Str(validate=validate.Length(max=10))
    city = fields.Str(validate=validate.Length(max=255))
    state = fields.Str(validate=validate.Length(max=255))
    country = fields.Str(validate=validate.Length(max=255))
    latitude = NumericStr(
        validate=validate.Range(-90, 90, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Latitude between (-90, 90)"},
        allow_none=True,
    )
    longitude = NumericStr(
        validate=validate.Range(-180, 180, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Longitude between (-180, 180)"},
        allow_none=True,
    )


class LocationSchema(LocationModelSchema, LocationBaseSchemaMixin):
    pass


class LocationDumpSchema(LocationSchema):
    pass


class LocationSearchItemSchema(LocationSchema):
    pass


class LocationPostRequestSchema(LocationModelSchema, LocationBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class LocationPatchRequestSchema(LocationModelSchema, LocationBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()


class LocationCreateRequestPlainSchema(
    PlainBaseSchema, LocationCoordinateValidationMixin
):
    street = fields.Str(load_default=None, validate=validate.Length(max=255))
    postalCode = fields.Str(load_default=None, validate=validate.Length(max=10))
    city = fields.Str(load_default=None, validate=validate.Length(max=255))
    state = fields.Str(load_default=None, validate=validate.Length(max=255))
    country = fields.Str(load_default=None, validate=validate.Length(max=255))
    latitude = NumericStr(
        load_default=None,
        validate=validate.Range(-90, 90, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Latitude between (-90, 90)"},
    )
    longitude = NumericStr(
        load_default=None,
        validate=validate.Range(-180, 180, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Longitude between (-180, 180)"},
    )

    @post_load
    def make_instance(self, data, **kwargs):
        return CreateLocation(**data)


class LocationPutRequestPlainSchema(PlainBaseSchema, LocationCoordinateValidationMixin):
    street = fields.Str(load_default=None, validate=validate.Length(max=255))
    postalCode = fields.Str(load_default=None, validate=validate.Length(max=10))
    city = fields.Str(load_default=None, validate=validate.Length(max=255))
    state = fields.Str(load_default=None, validate=validate.Length(max=255))
    country = fields.Str(load_default=None, validate=validate.Length(max=255))
    latitude = NumericStr(
        load_default=None,
        validate=validate.Range(-90, 90, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Latitude between (-90, 90)"},
    )
    longitude = NumericStr(
        load_default=None,
        validate=validate.Range(-180, 180, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Longitude between (-180, 180)"},
    )

    @post_load
    def make_instance(self, data, **kwargs):
        return UpdateLocation(**data)


class LocationPatchRequestPlainSchema(
    PlainBaseSchema, LocationCoordinateValidationMixin
):
    street = fields.Str(
        load_default=unset, allow_none=True, validate=validate.Length(max=255)
    )
    postalCode = fields.Str(
        load_default=unset, allow_none=True, validate=validate.Length(max=10)
    )
    city = fields.Str(
        load_default=unset, allow_none=True, validate=validate.Length(max=255)
    )
    state = fields.Str(
        load_default=unset, allow_none=True, validate=validate.Length(max=255)
    )
    country = fields.Str(
        load_default=unset, allow_none=True, validate=validate.Length(max=255)
    )
    latitude = NumericStr(
        load_default=unset,
        allow_none=True,
        validate=validate.Range(-90, 90, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Latitude between (-90, 90)"},
    )
    longitude = NumericStr(
        load_default=unset,
        allow_none=True,
        validate=validate.Range(-180, 180, min_inclusive=False, max_inclusive=False),
        metadata={"description": "Longitude between (-180, 180)"},
    )

    @post_load
    def make_instance(self, data, **kwargs):
        return UpdateLocation(**data)
