from project.domain.types import ObjectId

from .base import Command


class DeleteOrganizationCommand(Command):
    id: ObjectId
