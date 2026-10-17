from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.types.object_id import ObjectId


class EventVisibilityReadModel(BaseReadModel):
    """The facts `EventVisibilityService` decides readability from."""

    model_config = ConfigDict(frozen=True)

    event_id: ObjectId
    public_status: EventPublicStatus
    admin_unit_id: ObjectId
    admin_unit_is_verified: bool
