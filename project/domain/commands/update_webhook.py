from typing import Optional

from project.domain.types import Unsetable
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.unset_field_factory import UnsetField


class UpdateWebhook(CustomBaseModel):
    url: Unsetable[str] = UnsetField()
    secret: Unsetable[Optional[str]] = UnsetField()
    disabled: Unsetable[bool] = UnsetField()
    event_types: Unsetable[list[str]] = UnsetField()
