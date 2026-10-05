from datetime import datetime
from typing import Optional

from pydantic import model_validator

from project.domain.dateutils import sanitize_allday_instance
from project.domain.types.custom_base_model import CustomBaseModel


class EventDateDefinitionValueObject(CustomBaseModel):
    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
    recurrence_rule: Optional[str] = None

    @model_validator(mode="after")
    def sanitize(self) -> "EventDateDefinitionValueObject":
        sanitize_allday_instance(self)
        return self
