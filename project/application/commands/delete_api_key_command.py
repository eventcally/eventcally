from project.domain.types import ObjectId

from .base import Command


class DeleteApiKeyCommand(Command):
    id: ObjectId
