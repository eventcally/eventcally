from typing import List

from project.domain.types import ObjectId

from .base import Command


class ChangeOrganizationMemberRolesCommand(Command):
    id: ObjectId
    roles: List[str]
