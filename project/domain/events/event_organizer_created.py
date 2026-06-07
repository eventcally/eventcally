from typing import Optional

from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId

from .base import Event


class EventOrganizerCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationValueObject] = None
    logo: Optional[ImageForEvent] = None
