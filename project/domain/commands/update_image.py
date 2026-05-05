from typing import Optional

from project.domain.types import Unsetable
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.unset_field_factory import UnsetField


class UpdateImage(CustomBaseModel):
    data: Unsetable[bytes] = UnsetField()
    encoding_format: Unsetable[str] = UnsetField()
    copyright_text: Unsetable[Optional[str]] = UnsetField()
    license_id: Unsetable[Optional[int]] = UnsetField()
