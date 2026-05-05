from typing import Optional

from pydantic import ConfigDict

from project.domain.types.custom_base_model import CustomBaseModel

from .object_id import ObjectId


class Actor(CustomBaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: Optional[ObjectId] = None
    app_installation_id: Optional[ObjectId] = None
