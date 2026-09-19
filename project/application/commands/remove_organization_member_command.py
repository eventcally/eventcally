from project.domain.types import ObjectId

from .base import Command


class RemoveOrganizationMemberCommand(Command):
    id: ObjectId
