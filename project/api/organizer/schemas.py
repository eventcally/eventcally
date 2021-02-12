from marshmallow import fields, validate

from project.api import marshmallow
from project.api.image.schemas import ImageSchema
from project.api.location.schemas import (
    LocationPatchRequestSchema,
    LocationPostRequestSchema,
    LocationSchema,
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
from project.models import EventOrganizer


class OrganizerModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventOrganizer
        load_instance = True


class OrganizerIdSchema(OrganizerModelSchema, IdSchemaMixin):
    pass


class OrganizerWriteIdSchema(OrganizerModelSchema, WriteIdSchemaMixin):
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


class OrganizerPostRequestSchema(OrganizerModelSchema, OrganizerBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    location = fields.Nested(LocationPostRequestSchema)


class OrganizerPatchRequestSchema(OrganizerModelSchema, OrganizerBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()

    location = fields.Nested(LocationPatchRequestSchema)
