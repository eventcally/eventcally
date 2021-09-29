from marshmallow import fields, post_dump

from project.access import has_access, login_api_user
from project.api import marshmallow
from project.api.image.schemas import ImageDumpSchema, ImageSchema
from project.api.location.schemas import LocationDumpSchema, LocationSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    WriteIdSchemaMixin,
)
from project.models import AdminUnit


class OrganizationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AdminUnit
        load_instance = True


class OrganizationIdSchema(OrganizationModelSchema, IdSchemaMixin):
    pass


class OrganizationWriteIdSchema(OrganizationModelSchema, WriteIdSchemaMixin):
    pass


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
    can_verify_other = marshmallow.auto_field()

    @post_dump(pass_original=True)
    def remove_private_fields(self, data, original_data, **kwargs):
        login_api_user()
        if not has_access(original_data, "admin_unit:update"):
            data.pop("can_verify_other", None)

        return data


class OrganizationDumpSchema(OrganizationBaseSchema):
    location = fields.Nested(LocationDumpSchema)
    logo = fields.Nested(ImageDumpSchema)


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
