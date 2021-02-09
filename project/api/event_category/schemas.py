from marshmallow import fields
from project.api import marshmallow
from project.models import EventCategory
from project.api.schemas import (
    SQLAlchemyBaseSchema,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    WriteIdSchemaMixin,
)


class EventCategoryModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventCategory
        load_instance = True


class EventCategoryIdSchema(EventCategoryModelSchema, IdSchemaMixin):
    pass


class EventCategoryRefSchema(EventCategoryIdSchema):
    name = marshmallow.auto_field()


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
