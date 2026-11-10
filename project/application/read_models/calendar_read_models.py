from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class CalendarListItemReadModel(BaseReadModel):
    """A row of the calendar list (API and manage)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    description: Optional[str] = None
    private: bool = False
    number_of_events: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None


class CalendarReadModel(BaseReadModel):
    """One calendar with its organization (API detail, manage form values)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    admin_unit: OrganizationRefReadModel
    name: str
    description: Optional[str] = None
    private: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CalendarFilterInfo(BaseReadModel):
    """What the calendar search filter needs to decide who may filter by a calendar."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    private: bool


class CalendarRefReadModel(BaseReadModel):
    """A public calendar with its organization (the "In calendars" block)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    organization: OrganizationRefReadModel
