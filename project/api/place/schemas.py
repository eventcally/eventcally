from marshmallow import fields, post_load, validate

from project.api import marshmallow
from project.api.fields import Owned
from project.api.image.schemas import ImageDumpSchema, ImageSchema
from project.api.location.schemas import (
    LocationCreateRequestPlainSchema,
    LocationDumpSchema,
    LocationPatchRequestPlainSchema,
    LocationPatchRequestSchema,
    LocationPostRequestSchema,
    LocationPutRequestPlainSchema,
    LocationSchema,
    LocationSearchItemSchema,
)
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdPlainSchemaMixin,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
    WriteIdSchemaMixin,
)
from project.domain.commands import CreateEventPlaceCommand, UpdateEventPlaceCommand
from project.domain.types import unset
from project.models import EventPlace


class PlaceModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventPlace
        load_instance = True


class PlaceIdSchema(PlaceModelSchema, IdSchemaMixin):
    pass


class PlaceIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
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
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


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


class PlaceCreateRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(
        load_default=None, validate=[validate.URL(), validate.Length(max=255)]
    )
    description = fields.Str(load_default=None)
    location = fields.Nested(LocationCreateRequestPlainSchema, load_default=None)

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        return CreateEventPlaceCommand.model_construct(**data)


class PlacePutRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(
        load_default=None, validate=[validate.URL(), validate.Length(max=255)]
    )
    description = fields.Str(load_default=None)
    location = fields.Nested(LocationPutRequestPlainSchema, load_default=None)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        return UpdateEventPlaceCommand.model_construct(**data)


class PlacePatchRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(
        load_default=unset, allow_none=True, validate=validate.Length(min=3, max=255)
    )
    url = fields.Str(
        load_default=unset,
        allow_none=True,
        validate=[validate.URL(), validate.Length(max=255)],
    )
    description = fields.Str(load_default=unset, allow_none=True)
    location = fields.Nested(
        LocationPatchRequestPlainSchema, load_default=unset, allow_none=True
    )

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        return UpdateEventPlaceCommand.model_construct(**data)
