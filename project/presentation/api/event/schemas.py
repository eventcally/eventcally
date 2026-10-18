from marshmallow import ValidationError, fields, post_load, validate
from marshmallow.decorators import pre_load
from marshmallow_enum import EnumField

from project.application.commands.create_event_command import CreateEventCommand
from project.application.commands.update_event_command import UpdateEventCommand
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.presentation.api import marshmallow
from project.presentation.api.custom_event_category.schemas import (
    CustomEventCategoryIdSchema,
    CustomEventCategoryRefSchema,
    CustomEventCategoryWriteIdSchema,
)
from project.presentation.api.event_category.schemas import (
    EventCategoryIdSchema,
    EventCategoryRefSchema,
    EventCategoryWriteIdSchema,
)
from project.presentation.api.event_date_definition.schemas import (
    EventDateDefinitionPlainSchema,
    EventDateDefinitionSchema,
)
from project.presentation.api.fields import CustomDateTimeField
from project.presentation.api.image.schemas import (
    ImageDumpSchema,
    ImageSchema,
    ImageWriteRequestPlainSchema,
)
from project.presentation.api.organization.schemas import (
    OrganizationRefSchema,
    OrganizationSearchItemSchema,
)
from project.presentation.api.organizer.schemas import (
    OrganizerDumpIdSchema,
    OrganizerRefSchema,
    OrganizerSearchItemSchema,
    OrganizerWriteIdSchema,
)
from project.presentation.api.place.schemas import (
    PlaceRefSchema,
    PlaceSearchItemSchema,
    PlaceWriteIdSchema,
)
from project.presentation.api.schemas import (
    IdPlainSchemaMixin,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
    WriteIdPlainSchema,
    WriteIdSchemaMixin,
)


class EventModelSchema(PlainBaseSchema):
    pass


class EventIdSchema(EventModelSchema, IdSchemaMixin):
    pass


class EventIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class EventWriteIdSchema(EventModelSchema, WriteIdSchemaMixin):
    def object_exists(self, object_id) -> bool:
        return _event_exists(object_id)


def _event_exists(event_id) -> bool:
    from flask import current_app

    from project.application.queries import EventExistsQuery

    if not isinstance(event_id, int):
        return False

    return current_app.container.cqrs.query_bus().handle(EventExistsQuery(id=event_id))


class EventWriteIdPlainSchema(WriteIdPlainSchema):
    @pre_load()
    def validate_exists(self, data, **kwargs):
        if not _event_exists(data.get("id")):
            raise ValidationError("Referenced object does not exist")
        return data


class EventBaseSchemaMixin(TrackableSchemaMixin):
    name = fields.String(
        required=True,
        validate=validate.Length(min=3, max=255),
        metadata={"description": "A short, meaningful name for the event."},
    )
    description = fields.String(
        allow_none=True,
        metadata={"description": "Description of the event"},
    )
    external_link = fields.String(
        allow_none=True,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={
            "description": "A link to an external website containing more information about the event."
        },
    )
    ticket_link = fields.String(
        allow_none=True,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={"description": "A link where tickets can be purchased."},
    )
    tags = fields.String(
        allow_none=True,
        metadata={
            "description": "Comma separated keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        },
    )
    kid_friendly = fields.Boolean(
        allow_none=True,
        load_default=False,
        metadata={"description": "If the event is particularly suitable for children."},
    )
    accessible_for_free = fields.Boolean(
        allow_none=True,
        load_default=False,
        metadata={"description": "If the event is accessible for free."},
    )
    age_from = fields.Integer(
        allow_none=True,
        metadata={"description": "The minimum age that participants should be."},
    )
    age_to = fields.Integer(
        allow_none=True,
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
        dump_only=True,
        dump_default=None,
        metadata={"description": "Deprecated. Always null."},
    )
    registration_required = fields.Boolean(
        allow_none=True,
        load_default=False,
        metadata={
            "description": "If the participants needs to register for the event."
        },
    )
    booked_up = fields.Boolean(
        allow_none=True,
        load_default=False,
        metadata={"description": "If the event is booked up or sold out."},
    )
    expected_participants = fields.Integer(
        allow_none=True,
        metadata={"description": "The estimated expected attendance."},
    )
    price_info = fields.String(
        allow_none=True,
        metadata={
            "description": "Price information in textual form. E.g., different prices for adults and children."
        },
    )
    public_status = EnumField(
        EventPublicStatus,
        load_default=EventPublicStatus.published,
        metadata={"description": "Public status of the event."},
    )


class EventCurrentOrganizationMixin(object):
    reference_id = fields.Method(
        "get_reference_id",
        metadata={
            "description": "Reference id, if event is referenced by current organization"
        },
    )
    internal_tags = fields.Method(
        "get_internal_tags",
        metadata={
            "description": "Comma separated keywords for internal use. These will not be published. Only visible with corresponding rights."
        },
    )

    def get_reference_id(self, event):
        # Filled by the query for the calling organization (`reference_admin_unit_id`).
        return getattr(event, "reference_id", None)

    def get_internal_tags(self, event):
        # Cleared by the query handler unless the caller may read private events.
        return getattr(event, "internal_tags", None)


class EventSchema(
    EventIdSchema,
    EventBaseSchemaMixin,
    EventCurrentOrganizationMixin,
):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    organizer = fields.Nested(OrganizerRefSchema)
    place = fields.Nested(PlaceRefSchema, attribute="event_place")
    photo = fields.Nested(ImageSchema)
    categories = fields.List(fields.Nested(EventCategoryRefSchema))
    custom_categories = fields.List(fields.Nested(CustomEventCategoryRefSchema))
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
    custom_category_ids = fields.Pluck(
        CustomEventCategoryIdSchema, "id", many=True, attribute="custom_categories"
    )
    co_organizer_ids = fields.Pluck(
        OrganizerDumpIdSchema, "id", many=True, attribute="co_organizers"
    )
    date_definitions = fields.List(fields.Nested(EventDateDefinitionSchema))


class EventRefSchema(EventIdSchema):
    name = fields.String(required=True, validate=validate.Length(max=255))


class EventSearchItemSchema(
    EventIdSchema,
    EventBaseSchemaMixin,
    EventCurrentOrganizationMixin,
    TrackableSchemaMixin,
):
    date_definitions = fields.List(fields.Nested(EventDateDefinitionSchema))
    photo = fields.Nested(ImageSchema)
    place = fields.Nested(PlaceSearchItemSchema, attribute="event_place")
    organizer = fields.Nested(OrganizerSearchItemSchema)
    organization = fields.Nested(OrganizationSearchItemSchema, attribute="admin_unit")
    categories = fields.List(fields.Nested(EventCategoryRefSchema))
    custom_categories = fields.List(fields.Nested(CustomEventCategoryRefSchema))


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
    custom_category_set_id = fields.List(
        fields.Int(),
        metadata={
            "description": "Looks for events with custom categories from set with this id."
        },
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
        EnumField(EventPublicStatus),
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
    custom_categories = fields.List(
        fields.Nested(CustomEventCategoryWriteIdSchema),
        metadata={"description": "Custom categories that fit the event."},
    )
    rating = fields.Integer(
        allow_none=True,
        load_default=50,
        dump_default=50,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 50 (Default), 100 (Highlight)."
        },
    )
    internal_tags = fields.String(
        allow_none=True,
        metadata={
            "description": "Comma separated keywords for internal use. These will not be published. Only visible with corresponding rights."
        },
    )


class EventCreateRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=255),
        metadata={"description": "A short, meaningful name for the event."},
    )
    description = fields.Str(
        load_default=None,
        metadata={"description": "Description of the event"},
    )
    external_link = fields.Str(
        load_default=None,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={
            "description": "A link to an external website containing more information about the event."
        },
    )
    ticket_link = fields.Str(
        load_default=None,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={"description": "A link where tickets can be purchased."},
    )
    tags = fields.Str(
        load_default=None,
        metadata={
            "description": "Comma separated keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        },
    )
    kid_friendly = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is particularly suitable for children."},
    )
    accessible_for_free = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is accessible for free."},
    )
    age_from = fields.Int(
        load_default=None,
        metadata={"description": "The minimum age that participants should be."},
    )
    age_to = fields.Int(
        load_default=None,
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
    registration_required = fields.Bool(
        load_default=False,
        metadata={
            "description": "If the participants needs to register for the event."
        },
    )
    booked_up = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is booked up or sold out."},
    )
    expected_participants = fields.Int(
        load_default=None,
        metadata={"description": "The estimated expected attendance."},
    )
    price_info = fields.Str(
        load_default=None,
        metadata={
            "description": "Price information in textual form. E.g., different prices for adults and children."
        },
    )
    public_status = EnumField(
        EventPublicStatus,
        load_default=EventPublicStatus.published,
        metadata={"description": "Public status of the event."},
    )
    date_definitions = fields.List(
        fields.Nested(EventDateDefinitionPlainSchema),
        dump_default=None,
        required=True,
        validate=[validate.Length(min=1)],
        metadata={"description": "At least one date definition."},
    )
    photo = fields.Nested(
        ImageWriteRequestPlainSchema,
        load_default=None,
    )
    organizer = fields.Nested(
        WriteIdPlainSchema,
        attribute="organizer_id",
        required=True,
        metadata={"description": "Who is organizing the event."},
    )
    co_organizers = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="co_organizer_ids",
        metadata={"description": "Optional co-organizers."},
    )
    place = fields.Nested(
        WriteIdPlainSchema,
        attribute="event_place_id",
        required=True,
        metadata={"description": "Where the event takes place."},
    )
    categories = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="category_ids",
        metadata={"description": "Categories that fit the event."},
    )
    custom_categories = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="custom_category_ids",
        metadata={"description": "Custom categories that fit the event."},
    )
    rating = fields.Int(
        load_default=50,
        dump_default=50,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 50 (Default), 100 (Highlight)."
        },
    )
    internal_tags = fields.Str(
        load_default=None,
        metadata={
            "description": "Comma separated keywords for internal use. These will not be published. Only visible with corresponding rights."
        },
    )

    @pre_load()
    def handle_deprecated_fields(self, data, **kwargs):
        if "start" in data:
            if "date_definitions" not in data:
                data["date_definitions"] = [{"start": data["start"]}]
            data.pop("start")
        data.pop("previous_start_date", None)
        return data

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return CreateEventCommand(**data)


class EventPutRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=255),
        metadata={"description": "A short, meaningful name for the event."},
    )
    description = fields.Str(
        load_default=None,
        metadata={"description": "Description of the event"},
    )
    external_link = fields.Str(
        load_default=None,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={
            "description": "A link to an external website containing more information about the event."
        },
    )
    ticket_link = fields.Str(
        load_default=None,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={"description": "A link where tickets can be purchased."},
    )
    tags = fields.Str(
        load_default=None,
        metadata={
            "description": "Comma separated keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        },
    )
    kid_friendly = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is particularly suitable for children."},
    )
    accessible_for_free = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is accessible for free."},
    )
    age_from = fields.Int(
        load_default=None,
        metadata={"description": "The minimum age that participants should be."},
    )
    age_to = fields.Int(
        load_default=None,
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
    registration_required = fields.Bool(
        load_default=False,
        metadata={
            "description": "If the participants needs to register for the event."
        },
    )
    booked_up = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is booked up or sold out."},
    )
    expected_participants = fields.Int(
        load_default=None,
        metadata={"description": "The estimated expected attendance."},
    )
    price_info = fields.Str(
        load_default=None,
        metadata={
            "description": "Price information in textual form. E.g., different prices for adults and children."
        },
    )
    public_status = EnumField(
        EventPublicStatus,
        load_default=EventPublicStatus.published,
        metadata={"description": "Public status of the event."},
    )
    date_definitions = fields.List(
        fields.Nested(EventDateDefinitionPlainSchema),
        dump_default=None,
        required=True,
        validate=[validate.Length(min=1)],
        metadata={"description": "At least one date definition."},
    )
    photo = fields.Nested(
        ImageWriteRequestPlainSchema,
        load_default=None,
    )
    organizer = fields.Nested(
        WriteIdPlainSchema,
        attribute="organizer_id",
        required=True,
        metadata={"description": "Who is organizing the event."},
    )
    co_organizers = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="co_organizer_ids",
        metadata={"description": "Optional co-organizers."},
    )
    place = fields.Nested(
        WriteIdPlainSchema,
        attribute="event_place_id",
        required=True,
        metadata={"description": "Where the event takes place."},
    )
    categories = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="category_ids",
        metadata={"description": "Categories that fit the event."},
    )
    custom_categories = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="custom_category_ids",
        metadata={"description": "Custom categories that fit the event."},
    )
    rating = fields.Int(
        load_default=50,
        dump_default=50,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 50 (Default), 100 (Highlight)."
        },
    )
    internal_tags = fields.Str(
        load_default=None,
        metadata={
            "description": "Comma separated keywords for internal use. These will not be published. Only visible with corresponding rights."
        },
    )

    @pre_load()
    def handle_deprecated_fields(self, data, **kwargs):
        if "start" in data:
            if "date_definitions" not in data:
                data["date_definitions"] = [{"start": data["start"]}]
            data.pop("start")
        data.pop("previous_start_date", None)
        return data

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateEventCommand(**data)


class EventPatchRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(
        allow_none=True,
        validate=validate.Length(min=3, max=255),
        metadata={"description": "A short, meaningful name for the event."},
    )
    description = fields.Str(
        allow_none=True,
        metadata={"description": "Description of the event"},
    )
    external_link = fields.Str(
        allow_none=True,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={
            "description": "A link to an external website containing more information about the event."
        },
    )
    ticket_link = fields.Str(
        allow_none=True,
        validate=[validate.URL(), validate.Length(max=255)],
        metadata={"description": "A link where tickets can be purchased."},
    )
    tags = fields.Str(
        allow_none=True,
        metadata={
            "description": "Comma separated keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        },
    )
    kid_friendly = fields.Bool(
        allow_none=True,
        metadata={"description": "If the event is particularly suitable for children."},
    )
    accessible_for_free = fields.Bool(
        allow_none=True,
        metadata={"description": "If the event is accessible for free."},
    )
    age_from = fields.Int(
        allow_none=True,
        metadata={"description": "The minimum age that participants should be."},
    )
    age_to = fields.Int(
        allow_none=True,
        metadata={"description": "The maximum age that participants should be."},
    )
    target_group_origin = EnumField(
        EventTargetGroupOrigin,
        allow_none=True,
        metadata={
            "description": "Whether the event is particularly suitable for tourists or residents."
        },
    )
    attendance_mode = EnumField(
        EventAttendanceMode,
        allow_none=True,
        metadata={"description": "Choose how people can attend the event."},
    )
    status = EnumField(
        EventStatus,
        allow_none=True,
        metadata={"description": "Select the status of the event."},
    )
    registration_required = fields.Bool(
        allow_none=True,
        metadata={
            "description": "If the participants needs to register for the event."
        },
    )
    booked_up = fields.Bool(
        allow_none=True,
        metadata={"description": "If the event is booked up or sold out."},
    )
    expected_participants = fields.Int(
        allow_none=True,
        metadata={"description": "The estimated expected attendance."},
    )
    price_info = fields.Str(
        allow_none=True,
        metadata={
            "description": "Price information in textual form. E.g., different prices for adults and children."
        },
    )
    public_status = EnumField(
        EventPublicStatus,
        allow_none=True,
        metadata={"description": "Public status of the event."},
    )
    date_definitions = fields.List(
        fields.Nested(EventDateDefinitionPlainSchema),
        dump_default=None,
        allow_none=True,
        validate=[validate.Length(min=1)],
        metadata={"description": "At least one date definition."},
    )
    photo = fields.Nested(
        ImageWriteRequestPlainSchema,
        allow_none=True,
    )
    organizer = fields.Nested(
        WriteIdPlainSchema,
        attribute="organizer_id",
        allow_none=True,
        metadata={"description": "Who is organizing the event."},
    )
    co_organizers = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="co_organizer_ids",
        allow_none=True,
        metadata={"description": "Optional co-organizers."},
    )
    place = fields.Nested(
        WriteIdPlainSchema,
        attribute="event_place_id",
        allow_none=True,
        metadata={"description": "Where the event takes place."},
    )
    categories = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="category_ids",
        allow_none=True,
        metadata={"description": "Categories that fit the event."},
    )
    custom_categories = fields.List(
        fields.Nested(WriteIdPlainSchema),
        attribute="custom_category_ids",
        allow_none=True,
        metadata={"description": "Custom categories that fit the event."},
    )
    rating = fields.Int(
        allow_none=True,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 50 (Default), 100 (Highlight)."
        },
    )
    internal_tags = fields.Str(
        allow_none=True,
        metadata={
            "description": "Comma separated keywords for internal use. These will not be published. Only visible with corresponding rights."
        },
    )

    @pre_load()
    def handle_deprecated_fields(self, data, **kwargs):
        data.pop("previous_start_date", None)
        return data

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateEventCommand(**data)


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
        EventPublicStatus,
        load_default=EventPublicStatus.published,
        metadata={"description": "Public status of the event."},
    )
