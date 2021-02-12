from marshmallow import fields, validate

from project.api import marshmallow
from project.api.image.schemas import ImageSchema
from project.api.location.schemas import (
    LocationPatchRequestSchema,
    LocationPostRequestSchema,
    LocationSchema,
    LocationSearchItemSchema,
)
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableSchemaMixin,
    WriteIdSchemaMixin,
)
from project.models import EventPlace


class PlaceModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventPlace
        load_instance = True


class PlaceIdSchema(PlaceModelSchema, IdSchemaMixin):
    pass


class PlaceWriteIdSchema(PlaceModelSchema, WriteIdSchemaMixin):
    pass


class PlaceBaseSchemaMixin(TrackableSchemaMixin):
    name = marshmallow.auto_field(
        required=True, validate=validate.Length(min=3, max=255)
    )
    url = marshmallow.auto_field(validate=[validate.URL(), validate.Length(max=255)])
    description = marshmallow.auto_field()


class PlaceSchema(PlaceIdSchema, PlaceBaseSchemaMixin):
    location = fields.Nested(LocationSchema)
    photo = fields.Nested(ImageSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class PlaceDumpSchema(PlaceIdSchema, PlaceBaseSchemaMixin):
    location_id = fields.Int()
    photo_id = fields.Int()
    organization_id = fields.Int(attribute="admin_unit_id")


class PlaceRefSchema(PlaceIdSchema):
    name = marshmallow.auto_field()


class PlaceSearchItemSchema(PlaceRefSchema):
    location = fields.Nested(LocationSearchItemSchema)


class PlaceListRequestSchema(PaginationRequestSchema):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )


class PlaceListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(PlaceRefSchema), metadata={"description": "Places"}
    )


class PlacePostRequestSchema(PlaceModelSchema, PlaceBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    location = fields.Nested(LocationPostRequestSchema)


class PlacePatchRequestSchema(PlaceModelSchema, PlaceBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()

    location = fields.Nested(LocationPatchRequestSchema)
