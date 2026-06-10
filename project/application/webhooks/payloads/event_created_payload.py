"""Event created data model."""

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
from project.application.webhooks.payloads.webhook_value_mapping import map_list_value
from project.domain import events
from project.domain.types import ObjectId


class EventCreatedPayload(WebhookPayloadBase):
    id: ObjectId
    organization_id: ObjectId
    name: str
    organizer_id: ObjectId
    event_place_id: ObjectId
    photo: Optional[PayloadImage] = None
    date_definitions: List[PayloadEventDateDefinition]
    dates: List[PayloadEventDate]
    status: WebhookEventStatus = WebhookEventStatus.scheduled
    public_status: WebhookEventPublicStatus = WebhookEventPublicStatus.published
    description: Optional[str] = None
    external_link: Optional[str] = None
    ticket_link: Optional[str] = None
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    kid_friendly: Optional[bool] = None
    accessible_for_free: Optional[bool] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    registration_required: Optional[bool] = None
    booked_up: Optional[bool] = None
    expected_participants: Optional[int] = None
    price_info: Optional[str] = None
    target_group_origin: Optional[WebhookEventTargetGroupOrigin] = None
    attendance_mode: Optional[WebhookEventAttendanceMode] = None
    previous_start_date: Optional[datetime.datetime] = None
    category_ids: Optional[List[ObjectId]] = None
    custom_category_ids: Optional[List[ObjectId]] = None
    rating: Optional[int] = None
    co_organizer_ids: Optional[List[ObjectId]] = None

    @classmethod
    def from_event(cls, e: events.EventCreated, ctx: AbstractWebhookMapperContext):
        return cls(
            actor=PayloadActor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            organizer_id=e.organizer_id,
            event_place_id=e.event_place_id,
            photo=PayloadImage.from_event(e.photo, ctx),
            date_definitions=map_list_value(
                e.date_definitions, PayloadEventDateDefinition.from_value_object
            ),
            dates=map_list_value(e.dates, PayloadEventDate.from_entity),
            status=WebhookEventStatus.from_domain_enum(e.status),
            public_status=WebhookEventPublicStatus.from_domain_enum(e.public_status),
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
            target_group_origin=WebhookEventTargetGroupOrigin.from_domain_enum(
                e.target_group_origin
            ),
            attendance_mode=WebhookEventAttendanceMode.from_domain_enum(
                e.attendance_mode
            ),
            previous_start_date=e.previous_start_date,
            category_ids=e.category_ids,
            custom_category_ids=e.custom_category_ids,
            rating=e.rating,
            co_organizer_ids=e.co_organizer_ids,
        )
