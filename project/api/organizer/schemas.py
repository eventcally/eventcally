from marshmallow import fields, validate
from project.api import marshmallow
from project.models import EventOrganizer
from project.api.location.schemas import (
    LocationSchema,
    LocationPostRequestSchema,
    LocationPostRequestLoadSchema,
    LocationPatchRequestSchema,
    LocationPatchRequestLoadSchema,
)
from project.api.image.schemas import ImageSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema


class OrganizerIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    id = marshmallow.auto_field()


class OrganizerBaseSchema(OrganizerIdSchema):
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()
    name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    email = marshmallow.auto_field()
    phone = marshmallow.auto_field()
    fax = marshmallow.auto_field()


class OrganizerSchema(OrganizerBaseSchema):
    location = fields.Nested(LocationSchema)
    logo = fields.Nested(ImageSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class OrganizerDumpSchema(OrganizerBaseSchema):
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


class OrganizerPostRequestSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    url = fields.Str(validate=[validate.URL(), validate.Length(max=255)], missing=None)
    email = fields.Str(
        validate=[validate.Email(), validate.Length(max=255)], missing=None
    )
    phone = fields.Str(validate=validate.Length(max=255), missing=None)
    fax = fields.Str(validate=validate.Length(max=255), missing=None)

    location = fields.Nested(LocationPostRequestSchema, missing=None)


class OrganizerPostRequestLoadSchema(OrganizerPostRequestSchema):
    class Meta:
        model = EventOrganizer
        load_instance = True

    location = fields.Nested(LocationPostRequestLoadSchema, missing=None)


class OrganizerPatchRequestSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    name = fields.Str(validate=validate.Length(min=3, max=255), allow_none=True)
    url = fields.Str(
        validate=[validate.URL(), validate.Length(max=255)], allow_none=True
    )
    email = fields.Str(
        validate=[validate.Email(), validate.Length(max=255)], allow_none=True
    )
    phone = fields.Str(validate=validate.Length(max=255), allow_none=True)
    fax = fields.Str(validate=validate.Length(max=255), allow_none=True)
    location = fields.Nested(LocationPatchRequestSchema, allow_none=True)


class OrganizerPatchRequestLoadSchema(OrganizerPatchRequestSchema):
    class Meta:
        model = EventOrganizer
        load_instance = True

    location = fields.Nested(LocationPatchRequestLoadSchema, allow_none=True)
