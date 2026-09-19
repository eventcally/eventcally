from project.domain.types import ObjectId

from .base import Event


class MemberInvitationCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    email: str
