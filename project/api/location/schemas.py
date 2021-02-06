from marshmallow import validate, validates_schema, ValidationError
from project.api import marshmallow
from project.models import Location
from project.api.fields import NumericStr
from project.api.schemas import (
    SQLAlchemyBaseSchema,
    PostSchema,
    PatchSchema,
)


class LocationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = Location


class LocationBaseSchemaMixin(object):
    street = marshmallow.auto_field()
    postalCode = marshmallow.auto_field(validate=validate.Length(max=10))
    city = marshmallow.auto_field()
    state = marshmallow.auto_field()
    country = marshmallow.auto_field()
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

    @validates_schema
    def validate_location(self, data, **kwargs):
        lat_set = "latitude" in data and data["latitude"] is not None
        lon_set = "longitude" in data and data["longitude"] is not None

        if lat_set and not lon_set:
            raise ValidationError("If latitude is given, longitude is required.")

        if lon_set and not lat_set:
            raise ValidationError("If longitude is given, latitude is required.")


class LocationSchema(LocationModelSchema, LocationBaseSchemaMixin):
    pass


class LocationDumpSchema(LocationSchema):
    pass


class LocationSearchItemSchema(LocationSchema):
    pass


class LocationPostRequestSchema(
    PostSchema, LocationModelSchema, LocationBaseSchemaMixin
):
    pass


class LocationPatchRequestSchema(
    PatchSchema, LocationModelSchema, LocationBaseSchemaMixin
):
    pass
