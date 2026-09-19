from project.domain.types import ObjectId

from .base import Command


class AcceptMemberInvitationCommand(Command):
    id: ObjectId
