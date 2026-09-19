from project.domain.types import ObjectId

from .base import Command


class DeclineMemberInvitationCommand(Command):
    id: ObjectId
