from marshmallow import fields, validate

from project.api import marshmallow
from project.api.fields import Owned
from project.api.image.schemas import ImageDumpSchema, ImageSchema
from project.api.location.schemas import (
    LocationDumpSchema,
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
    TrackableRequestSchemaMixin,
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
    location = fields.Nested(LocationDumpSchema)
    photo = fields.Nested(ImageDumpSchema)
    organization_id = fields.Int(attribute="admin_unit_id")


class PlaceRefSchema(PlaceIdSchema):
    name = marshmallow.auto_field()


class PlaceSearchItemSchema(PlaceIdSchema, PlaceBaseSchemaMixin):
    location = fields.Nested(LocationSearchItemSchema)
    photo = fields.Nested(ImageSchema)


class PlaceListRequestSchema(PaginationRequestSchema, TrackableRequestSchemaMixin):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            ["-created_at", "-updated_at", "-last_modified_at", "name"]
        ),
    )


class PlaceListRefSchema(PlaceRefSchema, TrackableSchemaMixin):
    pass


class PlaceListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(PlaceListRefSchema), metadata={"description": "Places"}
    )


class PlacePostRequestSchema(PlaceModelSchema, PlaceBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    location = Owned(LocationPostRequestSchema)


class PlacePatchRequestSchema(PlaceModelSchema, PlaceBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()

    location = Owned(LocationPatchRequestSchema)
