from marshmallow import fields, validate

from project.api import marshmallow
from project.api.fields import Owned
from project.api.image.schemas import ImageDumpSchema, ImageSchema
from project.api.location.schemas import (
    LocationDumpSchema,
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
    TrackableRequestSchemaMixin,
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


class OrganizerDumpIdSchema(OrganizerModelSchema, IdSchemaMixin):
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
    location = fields.Nested(LocationDumpSchema)
    logo = fields.Nested(ImageDumpSchema)
    organization_id = fields.Int(attribute="admin_unit_id")


class OrganizerRefSchema(OrganizerIdSchema):
    name = marshmallow.auto_field()


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


class OrganizerPostRequestSchema(OrganizerModelSchema, OrganizerBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    location = Owned(LocationPostRequestSchema)


class OrganizerPatchRequestSchema(OrganizerModelSchema, OrganizerBaseSchemaMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()

    location = Owned(LocationPatchRequestSchema)
