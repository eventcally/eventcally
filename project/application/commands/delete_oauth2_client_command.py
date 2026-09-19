from project.domain.types import ObjectId

from .base import Command


class DeleteOAuth2ClientCommand(Command):
    id: ObjectId
