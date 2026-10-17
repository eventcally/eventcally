from marshmallow import fields, validate

from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    WriteIdSchemaMixin,
)


class EventCategoryModelSchema(PlainBaseSchema):
    pass


class EventCategoryIdSchema(EventCategoryModelSchema, IdSchemaMixin):
    pass


class EventCategoryRefSchema(EventCategoryIdSchema):
    name = fields.String(required=True, validate=validate.Length(max=255))


class EventCategoryWriteIdSchema(EventCategoryModelSchema, WriteIdSchemaMixin):
    pass


class EventCategoryDumpSchema(EventCategoryRefSchema):
    pass


class EventCategoryListRequestSchema(PaginationRequestSchema):
    pass


class EventCategoryListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventCategoryRefSchema),
        metadata={"description": "Event categories"},
    )
