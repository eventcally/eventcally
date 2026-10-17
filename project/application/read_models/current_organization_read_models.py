from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.image_read_model import ImageEditReadModel
from project.application.read_models.location_read_model import LocationReadModel
from project.domain.types.object_id import ObjectId


class CurrentOrganizationReadModel(BaseReadModel):
    """The organization a request acts for (the manage area, API calls on behalf of
    an organization): its identity and the flags pages and decisions read."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    short_name: Optional[str] = None
    is_verified: bool = False
    can_verify_other: bool = False
    can_invite_other: bool = False
    can_create_other: bool = False
    incoming_reference_requests_allowed: bool = False
    incoming_verification_requests_allowed: bool = False
    location: Optional[LocationReadModel] = None


class OrganizationSettingsReadModel(BaseReadModel):
    """Fills the organization settings and widget forms (attribute names equal the form
    field names) and backs the deletion pages."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationReadModel] = None
    logo: Optional[ImageEditReadModel] = None
    can_verify_other: bool = False
    incoming_verification_requests_allowed: bool = False
    incoming_verification_requests_text: Optional[str] = None
    incoming_verification_requests_postal_codes: List[str] = []
    widget_font: Optional[str] = None
    widget_background_color: Optional[str] = None
    widget_primary_color: Optional[str] = None
    widget_link_color: Optional[str] = None
    deletion_requested_at: Optional[datetime] = None
