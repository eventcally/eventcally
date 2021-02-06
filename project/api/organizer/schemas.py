from marshmallow import fields, validate
from project.api import marshmallow
from project.models import EventOrganizer
from project.api.location.schemas import (
    LocationSchema,
    LocationPostRequestSchema,
    LocationPatchRequestSchema,
)
from project.api.image.schemas import ImageSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    SQLAlchemyBaseSchema,
    IdSchemaMixin,
    TrackableSchemaMixin,
    PostSchema,
    PatchSchema,
    PaginationRequestSchema,
    PaginationResponseSchema,
)


class OrganizerModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventOrganizer


class OrganizerIdSchema(OrganizerModelSchema, IdSchemaMixin):
    pass


class OrganizerBaseSchemaMixin(TrackableSchemaMixin):
    name = marshmallow.auto_field(
        required=True, validate=validate.Length(min=3, max=255)
    )
    url = marshmallow.auto_field(validate=[validate.URL(), validate.Length(max=255)])
    email = marshmallow.auto_field(
        validate=[validate.Email(), validate.Length(max=255)]
    )
    phone = marshmallow.auto_field()
    fax = marshmallow.auto_field()


class OrganizerSchema(OrganizerIdSchema, OrganizerBaseSchemaMixin):
    location = fields.Nested(LocationSchema)
    logo = fields.Nested(ImageSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class OrganizerDumpSchema(OrganizerIdSchema, OrganizerBaseSchemaMixin):
    location_id = fields.Int()
    logo_id = fields.Int()
    organization_id = fields.Int(attribute="admin_unit_id")


class OrganizerRefSchema(OrganizerIdSchema):
    name = marshmallow.auto_field()


class OrganizerListRequestSchema(PaginationRequestSchema):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )


class OrganizerListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizerRefSchema), metadata={"description": "Organizers"}
    )


class OrganizerPostRequestSchema(
    PostSchema, OrganizerModelSchema, OrganizerBaseSchemaMixin
):
    location = fields.Nested(LocationPostRequestSchema, missing=None)


class OrganizerPatchRequestSchema(
    PatchSchema, OrganizerModelSchema, OrganizerBaseSchemaMixin
):
    location = fields.Nested(LocationPatchRequestSchema, allow_none=True)
