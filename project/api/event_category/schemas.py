from marshmallow import fields
from project.api import marshmallow
from project.models import EventCategory
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema


class EventCategoryIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventCategory

    id = marshmallow.auto_field()


class EventCategoryRefSchema(EventCategoryIdSchema):
    name = marshmallow.auto_field()


class EventCategoryDumpSchema(EventCategoryRefSchema):
    pass


class EventCategoryListRequestSchema(PaginationRequestSchema):
    pass


class EventCategoryListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventCategoryRefSchema),
        metadata={"description": "Event categories"},
    )
