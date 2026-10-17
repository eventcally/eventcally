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


class EventPlaceListItemReadModel(BaseReadModel):
    """A row of the manage list and of the API list (`PlaceListRefSchema`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    location: Optional[LocationReadModel] = None
    has_coordinates: bool = False
    has_photo: bool = False
    number_of_events: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None


class EventPlaceDetailReadModel(BaseReadModel):
    """The API detail (`PlaceSchema`); `admin_unit` feeds its `organization`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location: Optional[LocationReadModel] = None
    photo: Optional[ImageReadModel] = None
    admin_unit: OrganizationRefReadModel


class EventPlaceSuggestionReadModel(BaseReadModel):
    """An autocomplete entry; `get_place_str` reads only these fields."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    location: Optional[LocationReadModel] = None


class EventPlaceEditReadModel(BaseReadModel):
    """Fills the manage update form (attribute names equal the form field names) and
    backs the delete confirmation."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[LocationReadModel] = None
    photo: Optional[ImageEditReadModel] = None
