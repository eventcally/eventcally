from project import marshmallow
from marshmallow import fields
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
from project.api.image.schemas import ImageRefSchema
from project.api.place.schemas import PlaceRefSchema
from project.api.event_category.schemas import EventCategoryRefSchema


class EventSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")
    name = marshmallow.auto_field()
    description = marshmallow.auto_field()
    external_link = marshmallow.auto_field()
    ticket_link = marshmallow.auto_field()

    photo = fields.Nested(ImageRefSchema)
    categories = fields.List(fields.Nested(EventCategoryRefSchema))
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

    _links = marshmallow.Hyperlinks(
        {
            "dates": marshmallow.URLFor("eventdatesresource", values=dict(id="<id>")),
        }
    )


class EventRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    href = marshmallow.URLFor("eventresource", values=dict(id="<id>"))
    name = marshmallow.auto_field()


class EventListItemSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    href = marshmallow.URLFor("eventresource", values=dict(id="<id>"))
    name = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    recurrence_rule = marshmallow.auto_field()


class EventListRequestSchema(PaginationRequestSchema):
    pass


class EventListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventRefSchema), metadata={"description": "Events"}
    )
