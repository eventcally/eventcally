from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class AdminUnitReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str


class OrganizerReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str


class EventDateDefinitionReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
    recurrence_rule: Optional[str] = None


class EventReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    min_start_definition: EventDateDefinitionReadModel
    is_recurring: bool
    admin_unit: AdminUnitReadModel
    organizer: OrganizerReadModel
