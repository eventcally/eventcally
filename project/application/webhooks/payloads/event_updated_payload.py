"""Event updated data model."""

import datetime
from typing import List, Set

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.payloads.nested.payload_actor import PayloadActor
from project.application.webhooks.payloads.nested.payload_event_date import (
    PayloadEventDate,
)
from project.application.webhooks.payloads.nested.payload_event_date_definition import (
    PayloadEventDateDefinition,
)
from project.application.webhooks.payloads.nested.payload_image import PayloadImage
from project.application.webhooks.payloads.webhook_enums import (
    WebhookEventAttendanceMode,
    WebhookEventPublicStatus,
    WebhookEventStatus,
    WebhookEventTargetGroupOrigin,
)
from project.application.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.application.webhooks.payloads.webhook_value_mapping import (
    map_changed_list_value,
    map_changed_value,
)
from project.domain import events
from project.domain.types import ObjectId, OptionalChangedValue
from project.domain.types.changed_value import OptionalChangedOptionalValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class EventUpdatedPayload(WebhookPayloadBase):
    id: ObjectId
    organization_id: ObjectId
    name: OptionalChangedValue[str] = OptionalChangedValueField()
    photo: OptionalChangedOptionalValue[PayloadImage] = OptionalChangedValueField()
    organizer_id: OptionalChangedValue[ObjectId] = OptionalChangedValueField()
    event_place_id: OptionalChangedValue[ObjectId] = OptionalChangedValueField()
    date_definitions: OptionalChangedValue[List[PayloadEventDateDefinition]] = (
        OptionalChangedValueField()
    )
    dates: OptionalChangedValue[List[PayloadEventDate]] = OptionalChangedValueField()
    status: OptionalChangedValue[WebhookEventStatus] = OptionalChangedValueField()
    public_status: OptionalChangedValue[WebhookEventPublicStatus] = (
        OptionalChangedValueField()
    )
    description: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    external_link: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    ticket_link: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    tags: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    internal_tags: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    kid_friendly: OptionalChangedOptionalValue[bool] = OptionalChangedValueField()
    accessible_for_free: OptionalChangedOptionalValue[bool] = (
        OptionalChangedValueField()
    )
    age_from: OptionalChangedOptionalValue[int] = OptionalChangedValueField()
    age_to: OptionalChangedOptionalValue[int] = OptionalChangedValueField()
    registration_required: OptionalChangedOptionalValue[bool] = (
        OptionalChangedValueField()
    )
    booked_up: OptionalChangedOptionalValue[bool] = OptionalChangedValueField()
    expected_participants: OptionalChangedOptionalValue[int] = (
        OptionalChangedValueField()
    )
    price_info: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    target_group_origin: OptionalChangedOptionalValue[WebhookEventTargetGroupOrigin] = (
        OptionalChangedValueField()
    )
    attendance_mode: OptionalChangedOptionalValue[WebhookEventAttendanceMode] = (
        OptionalChangedValueField()
    )
    previous_start_date: OptionalChangedOptionalValue[datetime.datetime] = (
        OptionalChangedValueField()
    )
    category_ids: OptionalChangedValue[Set[ObjectId]] = OptionalChangedValueField()
    custom_category_ids: OptionalChangedValue[Set[ObjectId]] = (
        OptionalChangedValueField()
    )
    rating: OptionalChangedOptionalValue[int] = OptionalChangedValueField()
    co_organizer_ids: OptionalChangedValue[Set[ObjectId]] = OptionalChangedValueField()

    @classmethod
    def from_event(cls, e: events.EventUpdated, ctx: AbstractWebhookMapperContext):
        return cls(
            actor=PayloadActor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            photo=map_changed_value(
                e.photo, lambda img: PayloadImage.from_event(img, ctx)
            ),
            organizer_id=e.organizer_id,
            event_place_id=e.event_place_id,
            date_definitions=map_changed_list_value(
                e.date_definitions,
                PayloadEventDateDefinition.from_value_object,
            ),
            dates=map_changed_list_value(
                e.dates,
                PayloadEventDate.from_entity,
            ),
            status=map_changed_value(e.status, WebhookEventStatus.from_domain_enum),
            public_status=map_changed_value(
                e.public_status, WebhookEventPublicStatus.from_domain_enum
            ),
            description=e.description,
            external_link=e.external_link,
            ticket_link=e.ticket_link,
            tags=e.tags,
            internal_tags=e.internal_tags,
            kid_friendly=e.kid_friendly,
            accessible_for_free=e.accessible_for_free,
            age_from=e.age_from,
            age_to=e.age_to,
            registration_required=e.registration_required,
            booked_up=e.booked_up,
            expected_participants=e.expected_participants,
            price_info=e.price_info,
            target_group_origin=map_changed_value(
                e.target_group_origin, WebhookEventTargetGroupOrigin.from_domain_enum
            ),
            attendance_mode=map_changed_value(
                e.attendance_mode, WebhookEventAttendanceMode.from_domain_enum
            ),
            previous_start_date=e.previous_start_date,
            category_ids=e.category_ids,
            custom_category_ids=e.custom_category_ids,
            rating=e.rating,
            co_organizer_ids=e.co_organizer_ids,
        )
