from typing import Optional

from pydantic import BaseModel, ConfigDict

from .object_id import ObjectId


class Actor(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: Optional[ObjectId] = None
    app_installation_id: Optional[ObjectId] = None
