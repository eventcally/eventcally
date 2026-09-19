from project.domain.types import ObjectId

from .base import Event


class OrganizationInvitationAccepted(Event):
    id: ObjectId
    inviting_admin_unit_id: ObjectId
    new_admin_unit_id: ObjectId
    new_admin_unit_name: str
    accepting_user_email: str
