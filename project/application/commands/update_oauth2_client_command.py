from typing import List

from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateOAuth2ClientCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    redirect_uris: Unsetable[List[str]] = UnsetField()
    scope: NullableUnsetable[str] = UnsetField()
