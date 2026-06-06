from __future__ import annotations

from typing import Optional

from project.domain.events.event_organizer_created import EventOrganizerCreated
from project.domain.events.event_organizer_deleted import EventOrganizerDeleted
from project.domain.events.event_organizer_updated import EventOrganizerUpdated
from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import unset
from project.domain.types.changed_value import ChangedValue
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class EventOrganizerAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationValueObject] = None
    logo: Optional[ImageEntity] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        name: str,
        url: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        location: Optional[LocationValueObject] = None,
        logo: Optional[ImageEntity] = None,
    ) -> EventOrganizerAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            name=name,
            url=url,
            email=email,
            phone=phone,
            fax=fax,
            location=location,
            logo=logo,
        )

        event = EventOrganizerCreated(
            actor=actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            name=instance.name,
            url=instance.url,
            email=instance.email,
            phone=instance.phone,
            fax=instance.fax,
            location=instance.location,
            logo=(
                ImageForEvent.from_image_entity(instance.logo)
                if instance.logo
                else None
            ),
        )

        instance.domain_events.append(event)
        return instance

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
        url: NullableUnsetable[str] = unset,
        email: NullableUnsetable[str] = unset,
        phone: NullableUnsetable[str] = unset,
        fax: NullableUnsetable[str] = unset,
        location: NullableUnsetable[LocationValueObject] = unset,
        logo: NullableUnsetable[ImageEntity] = unset,
    ):
        event = EventOrganizerUpdated(
            actor=actor, id=self.id, admin_unit_id=self.admin_unit_id
        )

        self._update_field_with_value("name", name, event)
        self._update_field_with_value("url", url, event)
        self._update_field_with_value("email", email, event)
        self._update_field_with_value("phone", phone, event)
        self._update_field_with_value("fax", fax, event)
        self._update_field_with_value("location", location, event)

        old_logo_for_event = (
            ImageForEvent.from_image_entity(self.logo) if self.logo else None
        )
        if self._update_field_with_value("logo", logo):
            new_logo_for_event = (
                ImageForEvent.from_image_entity(self.logo) if self.logo else None
            )
            event.logo = ChangedValue(old=old_logo_for_event, new=new_logo_for_event)

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete(self, actor: Actor):
        self.domain_events.append(
            EventOrganizerDeleted(
                actor=actor, id=self.id, admin_unit_id=self.admin_unit_id
            )
        )
