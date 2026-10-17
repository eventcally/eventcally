from marshmallow import fields, validate

from project.presentation.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
)


class CustomEventCategorySetModelSchema(PlainBaseSchema):
    pass


class CustomEventCategorySetIdSchema(CustomEventCategorySetModelSchema, IdSchemaMixin):
    pass


class CustomEventCategorySetRefSchema(CustomEventCategorySetIdSchema):
    name = fields.String(required=True, validate=validate.Length(max=255))
    label = fields.String(allow_none=True, validate=validate.Length(max=255))


class CustomEventCategorySetDumpSchema(CustomEventCategorySetRefSchema):
    pass


class CustomEventCategorySetListRequestSchema(PaginationRequestSchema):
    pass


class CustomEventCategorySetListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(CustomEventCategorySetRefSchema),
        metadata={"description": "Custom event category sets"},
    )
