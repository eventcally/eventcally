from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class EventCategoryRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str


class CustomEventCategorySetRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    label: Optional[str] = None

    @property
    def label_or_name(self) -> str:
        return self.label or self.name


class CustomEventCategoryRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    label: Optional[str] = None
    category_set_id: ObjectId

    @property
    def label_or_name(self) -> str:
        return self.label or self.name
