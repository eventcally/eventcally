from marshmallow import fields

from project.api import marshmallow
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    WriteIdSchemaMixin,
)
from project.models import License


class LicenseModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = License
        load_instance = True


class LicenseIdSchema(LicenseModelSchema, IdSchemaMixin):
    pass


class LicenseRefSchema(LicenseIdSchema):
    name = marshmallow.auto_field()
    code = marshmallow.auto_field()
    url = marshmallow.auto_field()


class LicenseWriteIdSchema(LicenseModelSchema, WriteIdSchemaMixin):
    pass


class LicenseDumpSchema(LicenseRefSchema):
    pass


class LicenseListRequestSchema(PaginationRequestSchema):
    pass


class LicenseListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(LicenseRefSchema),
        metadata={"description": "Licenses"},
    )
