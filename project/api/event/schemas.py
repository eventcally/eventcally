from dateutil.rrule import rrulestr
from marshmallow import ValidationError, fields, validate
from marshmallow_enum import EnumField

from project.api import marshmallow
from project.api.event_category.schemas import (
    EventCategoryIdSchema,
    EventCategoryRefSchema,
    EventCategoryWriteIdSchema,
)
from project.api.fields import CustomDateTimeField
from project.api.image.schemas import ImageSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.organizer.schemas import OrganizerRefSchema, OrganizerWriteIdSchema
from project.api.place.schemas import (
    PlaceRefSchema,
    PlaceSearchItemSchema,
    PlaceWriteIdSchema,
)
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableSchemaMixin,
)
from project.models import (
    Event,
    EventAttendanceMode,
    EventStatus,
    EventTargetGroupOrigin,
)


class EventModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = Event
        load_instance = True


class EventIdSchema(EventModelSchema, IdSchemaMixin):
    pass


def validate_recurrence_rule(recurrence_rule):
    try:
        rrulestr(recurrence_rule, forceset=True)
    except Exception as e:
        raise ValidationError(str(e))


class EventBaseSchemaMixin(TrackableSchemaMixin):
    name = marshmallow.auto_field(
        required=True,
        validate=validate.Length(min=3, max=255),
        metadata={"description": "A short, meaningful name for the event."},
    )
    description = marshmallow.auto_field(
        metadata={"description": "Description of the event"},
    )
    external_link = marshmallow.auto_field(
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={
            "description": "A link to an external website containing more information about the event."
        },
    )
    ticket_link = marshmallow.auto_field(
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={"description": "A link where tickets can be purchased."},
    )
    tags = marshmallow.auto_field(
        metadata={
            "description": "Comma separated keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        }
    )
    kid_friendly = marshmallow.auto_field(
        missing=False,
        metadata={"description": "If the event is particularly suitable for children."},
    )
    accessible_for_free = marshmallow.auto_field(
        missing=False,
        metadata={"description": "If the event is accessible for free."},
    )
    age_from = marshmallow.auto_field(
        metadata={"description": "The minimum age that participants should be."},
    )
    age_to = marshmallow.auto_field(
        metadata={"description": "The maximum age that participants should be."},
    )
    target_group_origin = EnumField(
        EventTargetGroupOrigin,
        missing=EventTargetGroupOrigin.both,
        metadata={
            "description": "Whether the event is particularly suitable for tourists or residents."
        },
    )
    attendance_mode = EnumField(
        EventAttendanceMode,
        missing=EventAttendanceMode.offline,
        metadata={"description": "Choose how people can attend the event."},
    )
    status = EnumField(
        EventStatus,
        missing=EventStatus.scheduled,
        metadata={"description": "Select the status of the event."},
    )
    previous_start_date = CustomDateTimeField(
        metadata={
            "description": "When the event should have taken place before it was postponed."
        },
    )
    registration_required = marshmallow.auto_field(
        missing=False,
        metadata={
            "description": "If the participants needs to register for the event."
        },
    )
    booked_up = marshmallow.auto_field(
        missing=False,
        metadata={"description": "If the event is booked up or sold out."},
    )
    expected_participants = marshmallow.auto_field(
        metadata={"description": "The estimated expected attendance."},
    )
    price_info = marshmallow.auto_field(
        metadata={
            "description": "Price information in textual form. E.g., different prices for adults and children."
        },
    )
    recurrence_rule = marshmallow.auto_field(
        validate=validate_recurrence_rule,
        metadata={
            "description": "If the event takes place regularly. Format: RFC 5545."
        },
    )
    start = CustomDateTimeField(
        required=True,
        metadata={
            "description": "When the event will take place.  If the event takes place regularly, enter when the first date will begin."
        },
    )
    end = CustomDateTimeField(
        metadata={
            "description": "When the event will end. An event can last a maximum of 24 hours. If the event takes place regularly, enter when the first date will end."
        },
    )


class EventSchema(EventIdSchema, EventBaseSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")
    photo = fields.Nested(ImageSchema)
    categories = fields.List(fields.Nested(EventCategoryRefSchema))


class EventDumpSchema(EventIdSchema, EventBaseSchemaMixin):
    organization_id = fields.Int(attribute="admin_unit_id")
    organizer_id = fields.Int()
    place_id = fields.Int(attribute="event_place_id")
    photo_id = fields.Int()
    category_ids = fields.Pluck(
        EventCategoryIdSchema, "id", many=True, attribute="categories"
    )


class EventRefSchema(EventIdSchema):
    name = marshmallow.auto_field()


class EventSearchItemSchema(EventRefSchema):
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


class EventWriteSchemaMixin(object):
    organizer = fields.Nested(
        OrganizerWriteIdSchema,
        required=True,
        metadata={"description": "Who is organizing the event."},
    )
    place = fields.Nested(
        PlaceWriteIdSchema,
        required=True,
        attribute="event_place",
        metadata={"description": "Where the event takes place."},
    )
    categories = fields.List(
        fields.Nested(EventCategoryWriteIdSchema),
        metadata={"description": "Categories that fit the event."},
    )
    rating = marshmallow.auto_field(
        missing=50,
        default=50,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 5 (Default), 10 (Highlight)."
        },
    )


class EventPostRequestSchema(
    EventModelSchema, EventBaseSchemaMixin, EventWriteSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class EventPatchRequestSchema(
    EventModelSchema, EventBaseSchemaMixin, EventWriteSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()
