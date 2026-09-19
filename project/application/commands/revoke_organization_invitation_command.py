from project.domain.types import ObjectId

from .base import Command


class RevokeOrganizationInvitationCommand(Command):
    id: ObjectId
