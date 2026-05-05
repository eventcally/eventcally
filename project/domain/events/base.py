import datetime

from pydantic import Field

from project.domain.events.has_changed_value_mixin import HasChangedValueMixin
from project.domain.types import Actor
from project.domain.types.custom_base_model import CustomBaseModel


class Event(CustomBaseModel, HasChangedValueMixin):
    actor: Actor
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    def has_changed_values(self) -> bool:
        return self._has_set_changed_values()
