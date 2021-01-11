from marshmallow import fields
from project import marshmallow
from project.models import EventCategory
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema


class EventCategoryRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventCategory

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()


class EventCategoryListRequestSchema(PaginationRequestSchema):
    pass


class EventCategoryListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventCategoryRefSchema),
        metadata={"description": "Event categories"},
    )
