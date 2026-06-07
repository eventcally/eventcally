from datetime import datetime
from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class EventDateDefinitionValueObject(CustomBaseModel):
    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
    recurrence_rule: Optional[str] = None
