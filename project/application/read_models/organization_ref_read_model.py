from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class OrganizationRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str

    def __str__(self):
        # Displays render the organization itself, as the ORM `AdminUnit.__str__`.
        return self.name
