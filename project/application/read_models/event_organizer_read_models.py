from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.image_read_model import (
    ImageEditReadModel,
    ImageReadModel,
)
from project.application.read_models.location_read_model import LocationReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class EventOrganizerListItemReadModel(BaseReadModel):
    """A row of the manage list and of the API list (`OrganizerListRefSchema`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationReadModel] = None
    has_logo: bool = False
    number_of_events: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None


class EventOrganizerDetailReadModel(BaseReadModel):
    """The API detail (`OrganizerSchema`); `admin_unit` feeds its `organization`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location: Optional[LocationReadModel] = None
    logo: Optional[ImageReadModel] = None
    admin_unit: OrganizationRefReadModel


class EventOrganizerEditReadModel(BaseReadModel):
    """Fills the manage update form (attribute names equal the form field names) and
    backs the delete confirmation."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationReadModel] = None
    logo: Optional[ImageEditReadModel] = None


class EventOrganizerRefReadModel(BaseReadModel):
    """A select2 lookup entry and the value of a selected organizer field."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
