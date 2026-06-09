"""Event updated data model."""

import datetime
from typing import List, Optional

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
from project.domain.types import ChangedValue, ObjectId
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class EventUpdatedPayload(WebhookPayloadBase):
    id: ObjectId
    organization_id: ObjectId
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    photo: Optional[ChangedValue[PayloadImage]] = OptionalChangedValueField()
    organizer_id: Optional[ChangedValue[ObjectId]] = OptionalChangedValueField()
    event_place_id: Optional[ChangedValue[ObjectId]] = OptionalChangedValueField()
    date_definitions: Optional[ChangedValue[List[PayloadEventDateDefinition]]] = (
        OptionalChangedValueField()
    )
    dates: Optional[ChangedValue[List[PayloadEventDate]]] = OptionalChangedValueField()
    status: Optional[ChangedValue[WebhookEventStatus]] = OptionalChangedValueField()
    public_status: Optional[ChangedValue[WebhookEventPublicStatus]] = (
        OptionalChangedValueField()
    )
    description: Optional[ChangedValue[str]] = OptionalChangedValueField()
    external_link: Optional[ChangedValue[str]] = OptionalChangedValueField()
    ticket_link: Optional[ChangedValue[str]] = OptionalChangedValueField()
    tags: Optional[ChangedValue[str]] = OptionalChangedValueField()
    internal_tags: Optional[ChangedValue[str]] = OptionalChangedValueField()
    kid_friendly: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    accessible_for_free: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    age_from: Optional[ChangedValue[int]] = OptionalChangedValueField()
    age_to: Optional[ChangedValue[int]] = OptionalChangedValueField()
    registration_required: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    booked_up: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    expected_participants: Optional[ChangedValue[int]] = OptionalChangedValueField()
    price_info: Optional[ChangedValue[str]] = OptionalChangedValueField()
    target_group_origin: Optional[ChangedValue[WebhookEventTargetGroupOrigin]] = (
        OptionalChangedValueField()
    )
    attendance_mode: Optional[ChangedValue[WebhookEventAttendanceMode]] = (
        OptionalChangedValueField()
    )
    previous_start_date: Optional[ChangedValue[datetime.datetime]] = (
        OptionalChangedValueField()
    )
    category_ids: Optional[ChangedValue[List[ObjectId]]] = OptionalChangedValueField()
    custom_category_ids: Optional[ChangedValue[List[ObjectId]]] = (
        OptionalChangedValueField()
    )
    rating: Optional[ChangedValue[int]] = OptionalChangedValueField()
    co_organizer_ids: Optional[ChangedValue[List[ObjectId]]] = (
        OptionalChangedValueField()
    )

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
