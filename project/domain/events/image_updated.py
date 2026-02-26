from typing import Optional

from pydantic import BaseModel

from project.domain.events.has_changed_value_mixin import HasChangedValueMixin
from project.domain.types import ChangedValue


class ImageUpdated(BaseModel, HasChangedValueMixin):
    data_changed: bool = False
    encoding_format: Optional[ChangedValue[str]] = None
    copyright_text: Optional[ChangedValue[Optional[str]]] = None
    license_id: Optional[ChangedValue[Optional[int]]] = None

    def has_changed_values(self) -> bool:
        return self.data_changed or self._has_set_changed_values()
