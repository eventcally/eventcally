from project.domain.types import ObjectId

from .base import Command


class DeclineOrganizationInvitationCommand(Command):
    id: ObjectId
