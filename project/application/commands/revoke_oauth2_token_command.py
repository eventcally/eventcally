from project.domain.types import ObjectId

from .base import Command


class RevokeOAuth2TokenCommand(Command):
    id: ObjectId
