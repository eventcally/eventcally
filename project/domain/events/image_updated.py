from typing import Optional

from project.domain.events.has_changed_value_mixin import HasChangedValueMixin
from project.domain.types import ChangedValue
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.object_id import ObjectId
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class ImageUpdated(CustomBaseModel, HasChangedValueMixin):
    id: ObjectId
    hash: int
    data_changed: bool = False
    encoding_format: Optional[ChangedValue[str]] = OptionalChangedValueField()
    copyright_text: Optional[ChangedValue[Optional[str]]] = OptionalChangedValueField()
    license_id: Optional[ChangedValue[Optional[int]]] = OptionalChangedValueField()

    def has_changed_values(self) -> bool:
        return self.data_changed or self._has_set_changed_values()
