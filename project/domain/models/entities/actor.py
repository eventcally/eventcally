from typing import Optional

from pydantic import ConfigDict

from project.domain.models.entities.base_entity import BaseEntity

from ...types.object_id import ObjectId


class Actor(BaseEntity):
    model_config = ConfigDict(frozen=True)

    user_id: Optional[ObjectId] = None
    app_installation_id: Optional[ObjectId] = None
