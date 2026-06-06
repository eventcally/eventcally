from __future__ import annotations

from typing import Optional

from project.domain.events.event_place_created import EventPlaceCreated
from project.domain.events.event_place_deleted import EventPlaceDeleted
from project.domain.events.event_place_updated import EventPlaceUpdated
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


class EventPlaceAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[LocationValueObject] = None
    photo: Optional[ImageEntity] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        name: str,
        url: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[LocationValueObject] = None,
        photo: Optional[ImageEntity] = None,
    ) -> EventPlaceAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            name=name,
            url=url,
            description=description,
            location=location,
            photo=photo,
        )

        event = EventPlaceCreated(
            actor=actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            name=instance.name,
            url=instance.url,
            description=instance.description,
            location=instance.location,
            photo=(
                ImageForEvent.from_image_entity(instance.photo)
                if instance.photo
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
        description: NullableUnsetable[str] = unset,
        location: NullableUnsetable[LocationValueObject] = unset,
        photo: NullableUnsetable[ImageEntity] = unset,
    ):
        event = EventPlaceUpdated(
            actor=actor, id=self.id, admin_unit_id=self.admin_unit_id
        )

        self._update_field_with_value("name", name, event)
        self._update_field_with_value("url", url, event)
        self._update_field_with_value("description", description, event)
        self._update_field_with_value("location", location, event)

        old_photo_for_event = (
            ImageForEvent.from_image_entity(self.photo) if self.photo else None
        )
        if self._update_field_with_value("photo", photo):
            new_photo_for_event = (
                ImageForEvent.from_image_entity(self.photo) if self.photo else None
            )
            event.photo = ChangedValue(old=old_photo_for_event, new=new_photo_for_event)

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete(self, actor: Actor):
        self.domain_events.append(
            EventPlaceDeleted(actor=actor, id=self.id, admin_unit_id=self.admin_unit_id)
        )
