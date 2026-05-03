from typing import Optional

from project.domain.events.has_changed_value_mixin import HasChangedValueMixin
from project.domain.types import ChangedValue
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class WebhookUpdated(CustomBaseModel, HasChangedValueMixin):
    url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    secret: Optional[ChangedValue[Optional[str]]] = OptionalChangedValueField()
    disabled: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    event_types: Optional[ChangedValue[list[str]]] = OptionalChangedValueField()

    def has_changed_values(self) -> bool:
        return self._has_set_changed_values()
