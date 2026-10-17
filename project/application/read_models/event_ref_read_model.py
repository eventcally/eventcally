from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class EventRefReadModel(BaseReadModel):
    """An event as list rows link and name it (`EventProp`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    admin_unit: OrganizationRefReadModel

    def __str__(self):
        return self.name
