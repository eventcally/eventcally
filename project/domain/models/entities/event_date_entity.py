from __future__ import annotations

from typing import Optional

from project.domain.models.entities.base_entity import BaseEntity
from project.domain.types.named_zone_datetime import NamedZoneDatetime
from project.domain.types.object_id import ObjectId


class EventDateEntity(BaseEntity):
    id: ObjectId
    start: NamedZoneDatetime
    end: Optional[NamedZoneDatetime] = None
    allday: bool = False
