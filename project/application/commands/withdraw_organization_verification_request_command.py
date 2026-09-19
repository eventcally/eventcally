from project.domain.types import ObjectId

from .base import Command


class WithdrawOrganizationVerificationRequestCommand(Command):
    id: ObjectId
