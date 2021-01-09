from project import marshmallow
from marshmallow import fields
from marshmallow_enum import EnumField
from project.models import Event, EventStatus
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.organizer.schemas import OrganizerRefSchema
from project.api.image.schemas import ImageRefSchema
from project.api.place.schemas import PlaceRefSchema


class EventSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    href = marshmallow.URLFor("eventresource", values=dict(id="<id>"))
    name = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    recurrence_rule = marshmallow.auto_field()
    description = marshmallow.auto_field()
    external_link = marshmallow.auto_field()
    ticket_link = marshmallow.auto_field()
    tags = marshmallow.auto_field()
    kid_friendly = marshmallow.auto_field()
    accessible_for_free = marshmallow.auto_field()
    age_from = marshmallow.auto_field()
    age_to = marshmallow.auto_field()
    status = EnumField(EventStatus)

    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    photo = fields.Nested(ImageRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")


class EventRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    href = marshmallow.URLFor("eventresource", values=dict(id="<id>"))
    name = marshmallow.auto_field()
    description = marshmallow.auto_field()
    status = EnumField(EventStatus)

    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    photo = fields.Nested(ImageRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")


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
        fields.Nested(EventListItemSchema), metadata={"description": "Events"}
    )
