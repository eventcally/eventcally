from marshmallow import fields, validate

from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    WriteIdSchemaMixin,
)


class LicenseModelSchema(PlainBaseSchema):
    pass


class LicenseIdSchema(LicenseModelSchema, IdSchemaMixin):
    pass


class LicenseRefSchema(LicenseIdSchema):
    name = fields.String(allow_none=True, validate=validate.Length(max=255))
    code = fields.String(allow_none=True, validate=validate.Length(max=255))
    url = fields.String(allow_none=True, validate=validate.Length(max=255))


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
