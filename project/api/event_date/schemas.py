from marshmallow import fields, validate

from project.api import marshmallow
from project.api.event.schemas import (
    EventRefSchema,
    EventSearchItemSchema,
    EventSearchRequestSchema,
)
from project.api.fields import CustomDateTimeField
from project.api.schemas import (
    PaginationRequestSchema,
    PaginationResponseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
from project.models import EventDate


class EventDateSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventDate
        load_instance = True

    id = marshmallow.auto_field()
    start = CustomDateTimeField()
    end = CustomDateTimeField()
    allday = marshmallow.auto_field()
    event = fields.Nested(EventRefSchema)


class EventDateRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventDate
        load_instance = True

    id = marshmallow.auto_field()
    start = CustomDateTimeField()


class EventDateListRequestSchema(PaginationRequestSchema, TrackableRequestSchemaMixin):
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            [
                "-created_at",
                "-updated_at",
                "-last_modified_at",
                "start",
            ]
        ),
    )


class EventDateListRefSchema(EventDateRefSchema, TrackableSchemaMixin):
    pass


class EventDateListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventDateListRefSchema), metadata={"description": "Dates"}
    )


class EventDateSearchRequestSchema(EventSearchRequestSchema):
    pass


class EventDateSearchItemSchema(EventDateRefSchema):
    class Meta:
        model = EventDate
        load_instance = True

    end = CustomDateTimeField()
    allday = marshmallow.auto_field()
    event = fields.Nested(EventSearchItemSchema)


class EventDateSearchResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventDateSearchItemSchema), metadata={"description": "Dates"}
    )
