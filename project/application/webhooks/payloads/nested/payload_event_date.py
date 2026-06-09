"""Event date nested payload model."""

import datetime
from typing import Optional

from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.object_id import ObjectId


class PayloadEventDate(CustomBaseModel):
    id: ObjectId
    start: datetime.datetime
    end: Optional[datetime.datetime] = None
    allday: bool = False

    @classmethod
    def from_entity(cls, entity: EventDateEntity) -> "PayloadEventDate":
        return cls(
            id=entity.id,
            start=entity.start,
            end=entity.end,
            allday=entity.allday,
        )
