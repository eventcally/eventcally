from project.domain.types import ObjectId

from .base import Command


class UpdateAppInstallationPermissionsCommand(Command):
    id: ObjectId
    permissions: list[str]
