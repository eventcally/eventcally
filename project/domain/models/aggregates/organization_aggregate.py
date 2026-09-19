from __future__ import annotations

import datetime
from typing import List, Optional

from project.domain.events.organization_deletion_cancelled import (
    OrganizationDeletionCancelled,
)
from project.domain.events.organization_deletion_requested import (
    OrganizationDeletionRequested,
)
from project.domain.events.organization_updated import OrganizationUpdated
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class OrganizationAggregate(BaseAggregate):
    id: ObjectId
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    logo: Optional[ImageEntity] = None
    deletion_requested_at: Optional[datetime.datetime] = None
    deletion_requested_by_id: Optional[ObjectId] = None
    can_verify_other: bool = False
    can_create_other: bool = False
    can_invite_other: bool = False
    incoming_verification_requests_allowed: bool = False
    incoming_verification_requests_text: Optional[str] = None
    incoming_verification_requests_postal_codes: List[str] = []
    incoming_reference_requests_allowed: bool = False
    location: Optional[LocationValueObject] = None
    max_api_keys: int = 1
    widget_font: Optional[str] = None
    widget_background_color: Optional[str] = None
    widget_primary_color: Optional[str] = None
    widget_link_color: Optional[str] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        name: str,
        short_name: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        location: Optional[LocationValueObject] = None,
        logo: Optional[ImageEntity] = None,
    ) -> OrganizationAggregate:
        return cls(
            id=-1,
            name=name,
            short_name=short_name,
            description=description,
            url=url,
            email=email,
            phone=phone,
            fax=fax,
            location=location,
            logo=logo,
        )

    def request_deletion(
        self,
        actor: Actor,
    ):
        self.deletion_requested_at = datetime.datetime.utcnow()
        self.deletion_requested_by_id = actor.user_id

        event = OrganizationDeletionRequested(
            actor=actor,
            id=self.id,
        )
        self.domain_events.append(event)

    def cancel_deletion(
        self,
        actor: Actor,
    ):
        self.deletion_requested_at = None
        self.deletion_requested_by_id = None

        event = OrganizationDeletionCancelled(
            actor=actor,
            id=self.id,
        )
        self.domain_events.append(event)

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
        short_name: Unsetable[str] = unset,
        description: NullableUnsetable[str] = unset,
        url: NullableUnsetable[str] = unset,
        email: NullableUnsetable[str] = unset,
        phone: NullableUnsetable[str] = unset,
        fax: NullableUnsetable[str] = unset,
        location: NullableUnsetable[LocationValueObject] = unset,
        logo: NullableUnsetable[ImageEntity] = unset,
        incoming_verification_requests_allowed: Unsetable[bool] = unset,
        incoming_verification_requests_text: NullableUnsetable[str] = unset,
        incoming_verification_requests_postal_codes: Unsetable[List[str]] = unset,
        widget_font: NullableUnsetable[str] = unset,
        widget_background_color: NullableUnsetable[str] = unset,
        widget_primary_color: NullableUnsetable[str] = unset,
        widget_link_color: NullableUnsetable[str] = unset,
        incoming_reference_requests_allowed: Unsetable[bool] = unset,
        can_create_other: Unsetable[bool] = unset,
        can_invite_other: Unsetable[bool] = unset,
        can_verify_other: Unsetable[bool] = unset,
    ):
        self._update_field_with_value("name", name)
        self._update_field_with_value("short_name", short_name)
        self._update_field_with_value("description", description)
        self._update_field_with_value("url", url)
        self._update_field_with_value("email", email)
        self._update_field_with_value("phone", phone)
        self._update_field_with_value("fax", fax)
        self._update_field_with_value(
            "location", location, compare_fn=LocationValueObject.compare
        )
        self._update_field_with_value("logo", logo, compare_fn=ImageEntity.compare)
        self._update_field_with_value(
            "incoming_verification_requests_allowed",
            incoming_verification_requests_allowed,
        )
        self._update_field_with_value(
            "incoming_verification_requests_text",
            incoming_verification_requests_text,
        )
        self._update_field_with_value(
            "incoming_verification_requests_postal_codes",
            incoming_verification_requests_postal_codes,
        )
        self._update_field_with_value("widget_font", widget_font)
        self._update_field_with_value(
            "widget_background_color", widget_background_color
        )
        self._update_field_with_value("widget_primary_color", widget_primary_color)
        self._update_field_with_value("widget_link_color", widget_link_color)
        self._update_field_with_value(
            "incoming_reference_requests_allowed", incoming_reference_requests_allowed
        )
        self._update_field_with_value("can_create_other", can_create_other)
        self._update_field_with_value("can_invite_other", can_invite_other)
        self._update_field_with_value("can_verify_other", can_verify_other)

        self.validate_self()

        self.domain_events.append(OrganizationUpdated(actor=actor, id=self.id))

    def delete(self, actor: Actor):
        pass
