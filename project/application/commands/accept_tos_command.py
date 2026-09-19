from project.domain.types import ObjectId

from .base import Command


class AcceptTosCommand(Command):
    id: ObjectId
