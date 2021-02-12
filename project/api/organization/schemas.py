from marshmallow import fields

from project.api import marshmallow
from project.api.image.schemas import ImageSchema
from project.api.location.schemas import LocationSchema
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema
from project.models import AdminUnit


class OrganizationIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = AdminUnit
        load_instance = True

    id = marshmallow.auto_field()


class OrganizationBaseSchema(OrganizationIdSchema):
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()
    name = marshmallow.auto_field()
    short_name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    email = marshmallow.auto_field()
    phone = marshmallow.auto_field()
    fax = marshmallow.auto_field()


class OrganizationSchema(OrganizationBaseSchema):
    location = fields.Nested(LocationSchema)
    logo = fields.Nested(ImageSchema)


class OrganizationDumpSchema(OrganizationBaseSchema):
    location_id = fields.Int()
    logo_id = fields.Int()


class OrganizationRefSchema(OrganizationIdSchema):
    name = marshmallow.auto_field()


class OrganizationListRefSchema(OrganizationRefSchema):
    short_name = marshmallow.auto_field()


class OrganizationListRequestSchema(PaginationRequestSchema):
    keyword = fields.Str(
        metadata={"description": "Looks for keyword in name and short name."},
    )


class OrganizationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizationListRefSchema),
        metadata={"description": "Organizations"},
    )
