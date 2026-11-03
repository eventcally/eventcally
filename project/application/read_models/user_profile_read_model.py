from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class UserProfileReadModel(BaseReadModel):
    """The settings of a user as the profile and settings pages show them."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str
    locale: Optional[str] = None
    newsletter_enabled: bool = False
    deletion_requested_at: Optional[datetime] = None
    tos_accepted_at: Optional[datetime] = None
