from marshmallow import fields, validate
from marshmallow_enum import EnumField

from project.api.event.schemas import EventRefSchema, EventWriteIdSchema
from project.api.organization.schemas import (
    OrganizationRefSchema,
    OrganizationWriteIdSchema,
)
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
from project.models import EventReferenceRequest
from project.models.event_reference_request import (
    EventReferenceRequestRejectionReason,
    EventReferenceRequestReviewStatus,
)


class EventReferenceRequestModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventReferenceRequest
        load_instance = True


class EventReferenceRequestIdSchema(EventReferenceRequestModelSchema, IdSchemaMixin):
    pass


class EventReferenceRequestBaseSchemaMixin(TrackableSchemaMixin):
    review_status = EnumField(
        EventReferenceRequestReviewStatus,
        load_default=EventReferenceRequestReviewStatus.inbox,
    )
    rejection_reason = EnumField(
        EventReferenceRequestRejectionReason,
    )


class EventReferenceRequestRefSchema(
    EventReferenceRequestIdSchema, TrackableSchemaMixin
):
    event = fields.Nested(EventRefSchema)


class EventReferenceRequestSchema(
    EventReferenceRequestIdSchema, EventReferenceRequestBaseSchemaMixin
):
    event = fields.Nested(EventRefSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class EventReferenceRequestListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(["-created_at", "-updated_at", "-last_modified_at"]),
    )


class EventReferenceRequestListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventReferenceRequestRefSchema),
        metadata={"description": "Event reference requests"},
    )


class EventReferenceRequestWriteSchemaMixin(object):
    event = fields.Nested(
        EventWriteIdSchema,
        required=True,
        metadata={"description": "Event to reference"},
    )
    target_organization = fields.Nested(
        OrganizationWriteIdSchema,
        attribute="admin_unit",
        required=True,
        metadata={"description": "Target organization."},
    )


class EventReferenceRequestPostRequestSchema(
    EventReferenceRequestModelSchema,
    EventReferenceRequestWriteSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class EventReferenceRequestVerifyRequestSchema(SQLAlchemyBaseSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    rating = fields.Int(
        load_default=50,
        dump_default=50,
        validate=validate.OneOf([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        metadata={
            "description": "How relevant the event is to your organization. 0 (Little relevant), 50 (Default), 100 (Highlight)."
        },
    )


class EventReferenceRequestRejectRequestSchema(
    EventReferenceRequestModelSchema,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    rejection_reason = EnumField(
        EventReferenceRequestRejectionReason,
    )
