from project.api import marshmallow
from marshmallow import fields, validate
from marshmallow_enum import EnumField
from project.models import (
    Event,
    EventStatus,
    EventTargetGroupOrigin,
    EventAttendanceMode,
)
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.organizer.schemas import OrganizerRefSchema
from project.api.image.schemas import ImageSchema
from project.api.place.schemas import PlaceRefSchema, PlaceSearchItemSchema
from project.api.event_category.schemas import (
    EventCategoryRefSchema,
    EventCategoryIdSchema,
)


class EventBaseSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()

    name = marshmallow.auto_field()
    description = marshmallow.auto_field()
    external_link = marshmallow.auto_field()
    ticket_link = marshmallow.auto_field()

    tags = marshmallow.auto_field()
    kid_friendly = marshmallow.auto_field()
    accessible_for_free = marshmallow.auto_field()
    age_from = marshmallow.auto_field()
    age_to = marshmallow.auto_field()
    target_group_origin = EnumField(EventTargetGroupOrigin)
    attendance_mode = EnumField(EventAttendanceMode)
    status = EnumField(EventStatus)
    previous_start_date = marshmallow.auto_field()

    registration_required = marshmallow.auto_field()
    booked_up = marshmallow.auto_field()
    expected_participants = marshmallow.auto_field()
    price_info = marshmallow.auto_field()

    recurrence_rule = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()


class EventSchema(EventBaseSchema):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")
    photo = fields.Nested(ImageSchema)
    categories = fields.List(fields.Nested(EventCategoryRefSchema))


class EventDumpSchema(EventBaseSchema):
    organization_id = fields.Int(attribute="admin_unit_id")
    organizer_id = fields.Int()
    place_id = fields.Int(attribute="event_place_id")
    photo_id = fields.Int()
    category_ids = fields.Pluck(
        EventCategoryIdSchema, "id", many=True, attribute="categories"
    )


class EventRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()


class EventSearchItemSchema(EventRefSchema):
    class Meta:
        model = Event

    description = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    recurrence_rule = marshmallow.auto_field()
    photo = fields.Nested(ImageSchema)
    place = fields.Nested(PlaceSearchItemSchema, attribute="event_place")
    status = EnumField(EventStatus)
    booked_up = marshmallow.auto_field()
    organizer = fields.Nested(OrganizerRefSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    categories = fields.List(fields.Nested(EventCategoryRefSchema))


class EventListRequestSchema(PaginationRequestSchema):
    pass


class EventListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventRefSchema), metadata={"description": "Events"}
    )


class EventSearchRequestSchema(PaginationRequestSchema):
    keyword = fields.Str(
        metadata={"description": "Looks for keyword in name, description and tags."},
    )
    date_from = fields.Date(
        metadata={
            "description": "Looks for events at or after this date, e.g. 2020-12-31."
        },
    )
    date_to = fields.Date(
        metadata={
            "description": "Looks for events at or before this date, e.g. 2020-12-31."
        },
    )
    coordinate = fields.Str(
        metadata={
            "description": 'Looks for events around this coordinate. Expects comma separated latitude and longitude, e.g. "51.9077888,10.4333312". See distance.'
        },
    )
    distance = fields.Int(
        validate=validate.Range(min=1, max=100000),
        metadata={
            "description": "Looks for events around a coordinate within this distance. Expects distance in meters. See coordinate."
        },
    )
    category_id = fields.List(
        fields.Int(),
        metadata={"description": "Looks for events with this category ids."},
    )
    weekday = fields.List(
        fields.Int(validate=validate.Range(min=0, max=6)),
        metadata={
            "description": "Looks for events at this weekdays (0=Sunday, 1=Monday, ..)."
        },
    )


class EventSearchResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventSearchItemSchema), metadata={"description": "Events"}
    )
