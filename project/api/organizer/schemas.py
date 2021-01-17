from marshmallow import fields
from project import marshmallow
from project.models import EventOrganizer
from project.api.location.schemas import LocationRefSchema
from project.api.image.schemas import ImageRefSchema
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
    location = fields.Nested(LocationRefSchema)
    logo = fields.Nested(ImageRefSchema)
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
