from project.application.commands.base import Command
from project.domain.types import ObjectId


class CancelOrganizationDeletionCommand(Command):
    id: ObjectId
