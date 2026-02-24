import datetime

from pydantic import BaseModel, Field

from project.domain.types import Actor


class Event(BaseModel):
    actor: Actor
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    def has_changed_values(self) -> bool:
        return len(self.model_fields_set) > 0
