from project.domain.types import ObjectId

from .base import Command


class UninstallAppCommand(Command):
    id: ObjectId
