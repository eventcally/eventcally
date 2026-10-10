from typing import Optional

from pydantic import model_validator

from project.domain.dateutils import sanitize_allday_instance
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.named_zone_datetime import NamedZoneDatetime
from project.domain.types.text import NullableRecurrenceRule


class EventDateDefinitionValueObject(CustomBaseModel):
    start: NamedZoneDatetime
    end: Optional[NamedZoneDatetime] = None
    allday: bool = False
    recurrence_rule: NullableRecurrenceRule = None

    @model_validator(mode="after")
    def sanitize(self) -> "EventDateDefinitionValueObject":
        sanitize_allday_instance(self)
        return self
