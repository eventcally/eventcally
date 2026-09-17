from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import Unsetable

from .base import Command


class UpdateUserNotificationSettingsCommand(Command):
    id: ObjectId
    newsletter_enabled: Unsetable[bool] = UnsetField()
