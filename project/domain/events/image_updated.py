from typing import Optional

from pydantic import BaseModel

from project.domain.types import ChangedValue


class ImageUpdated(BaseModel):
    data: Optional[ChangedValue[bytes]] = None
    encoding_format: Optional[ChangedValue[str]] = None
    copyright_text: Optional[ChangedValue[Optional[str]]] = None
    license_id: Optional[ChangedValue[Optional[int]]] = None

    def has_changed_values(self) -> bool:
        return len(self.model_fields_set) > 0
