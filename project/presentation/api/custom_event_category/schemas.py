from marshmallow import fields, validate

from project.presentation.api.custom_event_category_set.schemas import (
    CustomEventCategorySetRefSchema,
)
from project.presentation.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    WriteIdSchemaMixin,
)


class CustomEventCategoryModelSchema(PlainBaseSchema):
    pass


class CustomEventCategoryIdSchema(CustomEventCategoryModelSchema, IdSchemaMixin):
    pass


class CustomEventCategoryRefSchema(CustomEventCategoryIdSchema):
    name = fields.String(required=True, validate=validate.Length(max=255))
    label = fields.String(allow_none=True, validate=validate.Length(max=255))
    category_set = fields.Nested(CustomEventCategorySetRefSchema)


class CustomEventCategoryWriteIdSchema(
    CustomEventCategoryModelSchema, WriteIdSchemaMixin
):
    pass


class CustomEventCategoryDumpSchema(CustomEventCategoryRefSchema):
    pass


class CustomEventCategoryListRequestSchema(PaginationRequestSchema):
    pass


class CustomEventCategoryListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(CustomEventCategoryRefSchema),
        metadata={"description": "Custom event categories"},
    )
