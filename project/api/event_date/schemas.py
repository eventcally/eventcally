from project import marshmallow
from marshmallow import fields
from project.models import EventDate
from project.api.event.schemas import EventSchema, EventRefSchema
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema


class EventDateSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventDate

    id = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    event = fields.Nested(EventSchema)


class EventDateListItemSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventDate

    id = marshmallow.auto_field()
    href = marshmallow.URLFor("eventdateresource", values=dict(id="<id>"))
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    event = fields.Nested(EventRefSchema)


class EventDateListRequestSchema(PaginationRequestSchema):
    pass


class EventDateListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventDateListItemSchema), metadata={"description": "Dates"}
    )
