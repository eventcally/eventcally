from __future__ import annotations

from datetime import datetime
from typing import Optional

from project.domain.models.entities.base_entity import BaseEntity
from project.domain.types.object_id import ObjectId


class EventDateEntity(BaseEntity):
    id: ObjectId
    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
