from marshmallow import fields, validate

from project.api.event.schemas import (
    EventRefSchema,
    EventSearchItemSchema,
    EventSearchRequestSchema,
)
from project.api.fields import CustomDateTimeField
from project.api.schemas import (
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)


class EventDateSchema(PlainBaseSchema):
    id = fields.Integer()
    start = CustomDateTimeField()
    end = CustomDateTimeField()
    allday = fields.Boolean()
    event = fields.Nested(EventRefSchema)


class EventDateRefSchema(PlainBaseSchema):
    id = fields.Integer()
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
    end = CustomDateTimeField()
    allday = fields.Boolean()
    event = fields.Nested(EventSearchItemSchema)


class EventDateSearchResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventDateSearchItemSchema), metadata={"description": "Dates"}
    )
