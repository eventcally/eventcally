from marshmallow import fields

from project.api import marshmallow
from project.api.event.schemas import (
    EventRefSchema,
    EventSearchItemSchema,
    EventSearchRequestSchema,
)
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema
from project.models import EventDate


class EventDateSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventDate
        load_instance = True

    id = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    event = fields.Nested(EventRefSchema)


class EventDateRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventDate
        load_instance = True

    id = marshmallow.auto_field()
    start = marshmallow.auto_field()


class EventDateListRequestSchema(PaginationRequestSchema):
    pass


class EventDateListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventDateRefSchema), metadata={"description": "Dates"}
    )


class EventDateSearchRequestSchema(EventSearchRequestSchema):
    pass


class EventDateSearchItemSchema(EventDateRefSchema):
    class Meta:
        model = EventDate
        load_instance = True

    end = marshmallow.auto_field()
    event = fields.Nested(EventSearchItemSchema)


class EventDateSearchResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventDateSearchItemSchema), metadata={"description": "Dates"}
    )
