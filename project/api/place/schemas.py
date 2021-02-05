from marshmallow import fields, validate
from project.api import marshmallow
from project.models import EventPlace
from project.api.image.schemas import ImageSchema
from project.api.location.schemas import (
    LocationSchema,
    LocationSearchItemSchema,
    LocationPostRequestSchema,
    LocationPostRequestLoadSchema,
    LocationPatchRequestSchema,
    LocationPatchRequestLoadSchema,
)
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema


class PlaceIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    id = marshmallow.auto_field()


class PlaceBaseSchema(PlaceIdSchema):
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()
    name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    description = marshmallow.auto_field()


class PlaceSchema(PlaceBaseSchema):
    location = fields.Nested(LocationSchema)
    photo = fields.Nested(ImageSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class PlaceDumpSchema(PlaceBaseSchema):
    location_id = fields.Int()
    photo_id = fields.Int()
    organization_id = fields.Int(attribute="admin_unit_id")


class PlaceRefSchema(PlaceIdSchema):
    name = marshmallow.auto_field()


class PlaceSearchItemSchema(PlaceRefSchema):
    class Meta:
        model = EventPlace

    location = fields.Nested(LocationSearchItemSchema)


class PlaceListRequestSchema(PaginationRequestSchema):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )


class PlaceListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(PlaceRefSchema), metadata={"description": "Places"}
    )


class PlacePostRequestSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(validate=[validate.URL(), validate.Length(max=255)], missing=None)
    description = fields.Str(missing=None)
    location = fields.Nested(LocationPostRequestSchema, missing=None)


class PlacePostRequestLoadSchema(PlacePostRequestSchema):
    class Meta:
        model = EventPlace
        load_instance = True

    location = fields.Nested(LocationPostRequestLoadSchema, missing=None)


class PlacePatchRequestSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    name = fields.Str(validate=validate.Length(min=3, max=255), allow_none=True)
    url = fields.Str(
        validate=[validate.URL(), validate.Length(max=255)], allow_none=True
    )
    description = fields.Str(allow_none=True)
    location = fields.Nested(LocationPatchRequestSchema, allow_none=True)


class PlacePatchRequestLoadSchema(PlacePatchRequestSchema):
    class Meta:
        model = EventPlace
        load_instance = True

    location = fields.Nested(LocationPatchRequestLoadSchema, allow_none=True)
