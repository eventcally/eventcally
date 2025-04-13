from flask_security import current_user
from marshmallow import fields, validate
from marshmallow.decorators import pre_load
from marshmallow_enum import EnumField

from project.api import marshmallow
from project.api.event_category.schemas import (
    EventCategoryIdSchema,
    EventCategoryRefSchema,
    EventCategoryWriteIdSchema,
)
from project.api.event_date_definition.schemas import (
    EventDateDefinitionPatchRequestSchema,
    EventDateDefinitionPostRequestSchema,
    EventDateDefinitionSchema,
)
from project.api.fields import CustomDateTimeField, Owned
from project.api.image.schemas import (
    ImageDumpSchema,
    ImagePatchRequestSchema,
    ImagePostRequestSchema,
    ImageSchema,
)
from project.api.organization.schemas import (
    OrganizationRefSchema,
    OrganizationSearchItemSchema,
)
from project.api.organizer.schemas import (
    OrganizerDumpIdSchema,
    OrganizerRefSchema,
    OrganizerSearchItemSchema,
    OrganizerWriteIdSchema,
)
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
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
    WriteIdSchemaMixin,
)
from project.models import (
    Event,
    EventAttendanceMode,
    EventStatus,
    EventTargetGroupOrigin,
    PublicStatus,
)


class EventModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = Event
        load_instance = True


class EventIdSchema(EventModelSchema, IdSchemaMixin):
    pass


class EventWriteIdSchema(EventModelSchema, WriteIdSchemaMixin):
    pass


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
        load_default=False,
        metadata={"description": "If the event is particularly suitable for children."},
    )
    accessible_for_free = marshmallow.auto_field(
        load_default=False,
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
        load_default=EventTargetGroupOrigin.both,
        metadata={
            "description": "Whether the event is particularly suitable for tourists or residents."
        },
    )
    attendance_mode = EnumField(
        EventAttendanceMode,
        load_default=EventAttendanceMode.offline,
        metadata={"description": "Choose how people can attend the event."},
    )
    status = EnumField(
        EventStatus,
        load_default=EventStatus.scheduled,
        metadata={"description": "Select the status of the event."},
    )
    previous_start_date = CustomDateTimeField(
        metadata={
            "description": "When the event should have taken place before it was postponed."
        },
    )
    registration_required = marshmallow.auto_field(
        load_default=False,
        metadata={
            "description": "If the participants needs to register for the event."
        },
    )
    booked_up = marshmallow.auto_field(
        load_default=False,
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
    public_status = EnumField(
        PublicStatus,
        load_default=PublicStatus.published,
        metadata={"description": "Public status of the event."},
    )


class EventCurrentUserMixin(object):
    is_favored = fields.Method(
        "get_is_favored",
        metadata={"description": "True, if event is favored by current user"},
    )

    def get_is_favored(self, event):
        if not current_user or not current_user.is_authenticated:
            return False

        from project.services.user import has_favorite_event

        return has_favorite_event(current_user.id, event.id)


class EventCurrentOrganizationMixin(object):
    reference_id = fields.Method(
        "get_reference_id",
        metadata={
            "description": "Reference id, if event is referenced by current organization"
        },
    )

    def get_reference_id(self, event):
        if not current_user or not current_user.is_authenticated:
            return None

        from project.views.utils import get_current_admin_unit_for_api

        admin_unit = get_current_admin_unit_for_api()

        if not admin_unit:
            return None

        from project.services.reference import get_event_reference

        reference = get_event_reference(event.id, admin_unit.id)
        return reference.id if reference is not None else None


class EventSchema(
    EventIdSchema,
    EventBaseSchemaMixin,
    EventCurrentUserMixin,
    EventCurrentOrganizationMixin,
):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")
    photo = fields.Nested(ImageSchema)
    categories = fields.List(fields.Nested(EventCategoryRefSchema))
    co_organizers = fields.List(fields.Nested(OrganizerRefSchema))
    date_definitions = fields.List(fields.Nested(EventDateDefinitionSchema))


class EventDumpSchema(EventIdSchema, EventBaseSchemaMixin):
    organization_id = fields.Int(attribute="admin_unit_id")
    organizer_id = fields.Int()
    place_id = fields.Int(attribute="event_place_id")
    photo = fields.Nested(ImageDumpSchema)
    category_ids = fields.Pluck(
        EventCategoryIdSchema, "id", many=True, attribute="categories"
    )
    co_organizer_ids = fields.Pluck(
        OrganizerDumpIdSchema, "id", many=True, attribute="co_organizers"
    )
    date_definitions = fields.List(fields.Nested(EventDateDefinitionSchema))


class EventRefSchema(EventIdSchema):
    name = marshmallow.auto_field()


class EventSearchItemSchema(
    EventIdSchema,
    EventBaseSchemaMixin,
    EventCurrentUserMixin,
    EventCurrentOrganizationMixin,
    TrackableSchemaMixin,
):
    date_definitions = fields.List(fields.Nested(EventDateDefinitionSchema))
    photo = fields.Nested(ImageSchema)
    place = fields.Nested(PlaceSearchItemSchema, attribute="event_place")
    organizer = fields.Nested(OrganizerSearchItemSchema)
    organization = fields.Nested(OrganizationSearchItemSchema, attribute="admin_unit")
    categories = fields.List(fields.Nested(EventCategoryRefSchema))


class EventListRequestSchema(PaginationRequestSchema, TrackableRequestSchemaMixin):
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


class EventListItemRefSchema(EventRefSchema, TrackableSchemaMixin):
    pass


class EventListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventListItemRefSchema), metadata={"description": "Events"}
    )


class UserFavoriteEventListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
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


class UserFavoriteEventListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventListItemRefSchema), metadata={"description": "Events"}
    )


class EventSearchRequestSchema(PaginationRequestSchema, TrackableRequestSchemaMixin):
    keyword = fields.Str(
        metadata={"description": "Looks for keyword in name, description and tags."},
    )
    tag = fields.List(
        fields.Str(),
        metadata={"description": "Looks for events having all given tags."},
    )
    internal_tag = fields.List(
        fields.Str(),
        metadata={
            "description": "Looks for events having all given internal tags. Only works with corresponding rights."
        },
    )
    date_from = fields.Date(
        metadata={
            "description": "Looks for events at or after this date, e.g. 2020-12-31."
        },
    )
    date_to = fields.Date(
        metadata={"description": "Looks for events before this date, e.g. 2020-12-31."},
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
    organization_id = fields.Int(
        metadata={"description": "Looks for events with this organization id."},
    )
    organizer_id = fields.Int(
        metadata={"description": "Looks for events with this organizer id."},
    )
    event_place_id = fields.Int(
        metadata={"description": "Looks for events with this event place id."},
    )
    event_list_id = fields.List(
        fields.Int(),
        metadata={"description": "Looks for events with this event list ids."},
    )
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            [
                "-created_at",
                "-updated_at",
                "-last_modified_at",
                "-rating",
                "-reference_created_at",
                "start",
            ]
        ),
    )
    status = fields.List(
        EnumField(EventStatus),
        metadata={"description": "Looks for events with this stati."},
    )
    public_status = fields.List(
        EnumField(PublicStatus),
        metadata={"description": "Looks for events with this public stati."},
    )
    postal_code = fields.List(
        fields.Str(),
        metadata={"description": "Looks for events with places with this postal code."},
    )
    exclude_recurring = fields.Bool(
        metadata={"description": "Exclude recurring events"},
    )
    include_organization_references = fields.Bool(
        metadata={
            "description": "Include events referenced by organization. Only valid if there is an organization context."
        },
    )
    organization_references_only = fields.Bool(
        metadata={
            "description": "Only events referenced by organization. Only valid if there is an organization context."
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
    co_organizers = fields.List(
        fields.Nested(OrganizerWriteIdSchema),
        metadata={"description": "Optional co-organizers."},
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
        load_default=50,
        dump_default=50,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 50 (Default), 100 (Highlight)."
        },
    )

    @pre_load()
    def handle_deprecated_fields(self, data, **kwargs):
        if "start" in data:
            if "date_definitions" not in data:
                data["date_definitions"] = [{"start": data["start"]}]
            data.pop("start")
        return data


class EventPostRequestSchema(
    EventModelSchema, EventBaseSchemaMixin, EventWriteSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    date_definitions = fields.List(
        fields.Nested(EventDateDefinitionPostRequestSchema),
        dump_default=None,
        required=True,
        validate=[validate.Length(min=1)],
        metadata={"description": "At least one date definition."},
    )
    photo = Owned(ImagePostRequestSchema)


class EventPatchRequestSchema(
    EventModelSchema, EventBaseSchemaMixin, EventWriteSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()

    date_definitions = fields.List(
        fields.Nested(EventDateDefinitionPatchRequestSchema),
        dump_default=None,
        required=True,
        validate=[validate.Length(min=1)],
        metadata={"description": "At least one date definition."},
    )
    photo = Owned(ImagePatchRequestSchema)


class EventReportPostSchema(marshmallow.Schema):
    contact_name = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=255),
    )
    contact_email = fields.Email(
        required=True, validate=[validate.Email(), validate.Length(max=255)]
    )
    message = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=1000),
    )


class EventImportRequestSchema(marshmallow.Schema):
    url = fields.URL(
        required=True,
        metadata={
            "description": "A link to an external website containing more information about the event."
        },
    )
    public_status = EnumField(
        PublicStatus,
        load_default=PublicStatus.published,
        metadata={"description": "Public status of the event."},
    )
