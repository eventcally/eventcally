from marshmallow import fields, post_load, validate

from project.api import marshmallow
from project.api.image.schemas import ImageDumpSchema, ImageSchema
from project.api.location.schemas import (
    LocationDumpSchema,
    LocationSchema,
    LocationSearchItemSchema,
    LocationWriteRequestPlainSchema,
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
from project.application.commands import (
    CreateEventOrganizerCommand,
    UpdateEventOrganizerCommand,
)
from project.models import EventOrganizer


class OrganizerModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventOrganizer
        load_instance = True


class OrganizerIdSchema(OrganizerModelSchema, IdSchemaMixin):
    pass


class OrganizerIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class OrganizerDumpIdSchema(OrganizerModelSchema, IdSchemaMixin):
    pass


class OrganizerWriteIdSchema(OrganizerModelSchema, WriteIdSchemaMixin):
    pass


class OrganizerBaseSchemaMixin(TrackableSchemaMixin):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(validate=[validate.URL(), validate.Length(max=255)])
    email = fields.Str(validate=[validate.Email(), validate.Length(max=255)])
    phone = fields.Str(validate=validate.Length(max=255))
    fax = fields.Str(validate=validate.Length(max=255))


class OrganizerSchema(OrganizerIdSchema, OrganizerBaseSchemaMixin):
    location = fields.Nested(LocationSchema)
    logo = fields.Nested(ImageSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class OrganizerDumpSchema(OrganizerIdSchema, OrganizerBaseSchemaMixin):
    location = fields.Nested(LocationDumpSchema)
    logo = fields.Nested(ImageDumpSchema)
    organization_id = fields.Int(attribute="admin_unit_id")


class OrganizerRefSchema(OrganizerIdSchema):
    name = marshmallow.auto_field()


class OrganizerSearchItemSchema(OrganizerIdSchema, OrganizerBaseSchemaMixin):
    location = fields.Nested(LocationSearchItemSchema)
    logo = fields.Nested(ImageSchema)


class OrganizerListRequestSchema(PaginationRequestSchema, TrackableRequestSchemaMixin):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            ["-created_at", "-updated_at", "-last_modified_at", "name"]
        ),
    )


class OrganizerListRefSchema(OrganizerRefSchema, TrackableSchemaMixin):
    pass


class OrganizerListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizerListRefSchema), metadata={"description": "Organizers"}
    )


class OrganizerCreateRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(
        load_default=None, validate=[validate.URL(), validate.Length(max=255)]
    )
    email = fields.Str(
        load_default=None, validate=[validate.Email(), validate.Length(max=255)]
    )
    phone = fields.Str(load_default=None, validate=validate.Length(max=255))
    fax = fields.Str(load_default=None, validate=validate.Length(max=255))
    location = fields.Nested(LocationWriteRequestPlainSchema, load_default=None)

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        return CreateEventOrganizerCommand.model_construct(**data)


class OrganizerPutRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(
        load_default=None, validate=[validate.URL(), validate.Length(max=255)]
    )
    email = fields.Str(
        load_default=None, validate=[validate.Email(), validate.Length(max=255)]
    )
    phone = fields.Str(load_default=None, validate=validate.Length(max=255))
    fax = fields.Str(load_default=None, validate=validate.Length(max=255))
    location = fields.Nested(LocationWriteRequestPlainSchema, load_default=None)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        return UpdateEventOrganizerCommand.model_construct(**data)


class OrganizerPatchRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(allow_none=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(
        allow_none=True,
        validate=[validate.URL(), validate.Length(max=255)],
    )
    email = fields.Str(
        allow_none=True,
        validate=[validate.Email(), validate.Length(max=255)],
    )
    phone = fields.Str(allow_none=True, validate=validate.Length(max=255))
    fax = fields.Str(allow_none=True, validate=validate.Length(max=255))
    location = fields.Nested(LocationWriteRequestPlainSchema, allow_none=True)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        return UpdateEventOrganizerCommand.model_construct(**data)
