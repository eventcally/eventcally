from project.domain.types import ObjectId

from .base import Command


class DeleteOrganizationRelationCommand(Command):
    id: ObjectId
