from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.image_read_model import ImageReadModel
from project.application.read_models.location_read_model import LocationReadModel
from project.domain.types.object_id import ObjectId


class OrganizationListItemReadModel(BaseReadModel):
    """A row of the organization search (`OrganizationListRefSchema`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    short_name: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationDetailReadModel(BaseReadModel):
    """The public organization profile (`OrganizationSchema`). The API drops the
    settings fields unless the caller has `settings:read`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    short_name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    description: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location: Optional[LocationReadModel] = None
    logo: Optional[ImageReadModel] = None
    can_verify_other: bool = False
    incoming_reference_requests_allowed: bool = False


class OrganizationWidgetSettingsReadModel(BaseReadModel):
    """The widget styles an organization configured (colors as hex strings)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    widget_font: Optional[str] = None
    widget_background_color: Optional[str] = None
    widget_primary_color: Optional[str] = None
    widget_link_color: Optional[str] = None
