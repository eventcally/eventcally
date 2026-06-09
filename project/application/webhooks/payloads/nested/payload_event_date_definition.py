"""Event date definition nested payload model."""

import datetime
from typing import Optional

from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types.custom_base_model import CustomBaseModel


class PayloadEventDateDefinition(CustomBaseModel):
    start: datetime.datetime
    end: Optional[datetime.datetime] = None
    allday: bool = False
    recurrence_rule: Optional[str] = None

    @classmethod
    def from_value_object(
        cls, vo: EventDateDefinitionValueObject
    ) -> "PayloadEventDateDefinition":
        return cls(
            start=vo.start,
            end=vo.end,
            allday=vo.allday,
            recurrence_rule=vo.recurrence_rule,
        )
