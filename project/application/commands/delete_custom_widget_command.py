from project.domain.types import ObjectId

from .base import Command


class DeleteCustomWidgetCommand(Command):
    id: ObjectId
