from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class UserAdminReadModel(BaseReadModel):
    """A user as the platform admin pages list and edit them."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str
    created_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    tos_accepted_at: Optional[datetime] = None
    deletion_requested_at: Optional[datetime] = None
    roles: List[str] = []


class RoleReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    title: str


class NewsletterRecipientReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str
    locale: Optional[str] = None
