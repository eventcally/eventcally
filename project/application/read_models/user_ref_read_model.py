from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class UserRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str

    def __str__(self):
        # Displays render the user itself, as the ORM `User.__str__` did.
        return self.email
