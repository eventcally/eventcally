from project.domain.types import ObjectId

from .base import Command


class LeaveOrganizationCommand(Command):
    id: ObjectId
