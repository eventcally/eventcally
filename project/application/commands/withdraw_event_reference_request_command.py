from project.domain.types import ObjectId

from .base import Command


class WithdrawEventReferenceRequestCommand(Command):
    id: ObjectId
