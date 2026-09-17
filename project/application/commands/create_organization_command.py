from typing import Optional

from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateOrganizationCommandResult(CommandResult):
    id: ObjectId
    verified: bool


class CreateOrganizationCommand(CommandWithResult[CreateOrganizationCommandResult]):
    name: str
    short_name: str
    description: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationValueObject] = None
    logo: Optional[ImageValueObject] = None
    invitation_id: Optional[ObjectId] = None
    current_admin_unit_id: Optional[ObjectId] = None
    embedded_relation_verify: bool = False
    embedded_relation_auto_verify_event_reference_requests: bool = False
