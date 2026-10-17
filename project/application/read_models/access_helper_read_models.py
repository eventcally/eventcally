from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class ManageMenuOptionsReadModel(BaseReadModel):
    """Badge counts of the manage bar (`layout.html`): inbox requests addressed to the
    organization."""

    model_config = ConfigDict(frozen=True)

    reference_requests_incoming_badge: int = 0
    verification_requests_incoming_badge: int = 0


class MemberGrantsReadModel(BaseReadModel):
    """Roles and permissions the actor holds in an organization (Vue
    `currentAdminUnit` in `layout_vue.html`). `permissions` concatenates the roles'
    permissions in role id order, duplicates kept."""

    model_config = ConfigDict(frozen=True)

    roles: List[str] = []
    permissions: List[str] = []


class MailRecipientReadModel(BaseReadModel):
    """A user a mail is sent to (event report mails)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str
    locale: Optional[str] = None
