from project.domain.types import ObjectId

from .base import Command


class RevokeMemberInvitationCommand(Command):
    id: ObjectId
