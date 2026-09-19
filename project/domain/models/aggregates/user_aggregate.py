from __future__ import annotations

import datetime
from typing import List, Optional

from project.domain.events.user_deletion_cancelled import UserDeletionCancelled
from project.domain.events.user_deletion_requested import UserDeletionRequested
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class UserAggregate(BaseAggregate):
    id: ObjectId
    email: str
    locale: Optional[str]
    is_platform_admin: bool = False
    max_api_keys: int = 1
    newsletter_enabled: bool = True
    deletion_requested_at: Optional[datetime.datetime] = None
    tos_accepted_at: Optional[datetime.datetime] = None
    roles: List[str] = []

    def update(
        self,
        actor: Actor,
        locale: NullableUnsetable[str] = unset,
        newsletter_enabled: Unsetable[bool] = unset,
        roles: Unsetable[List[str]] = unset,
    ):
        self._update_field_with_value("locale", locale)
        self._update_field_with_value("newsletter_enabled", newsletter_enabled)
        self._update_field_with_value("roles", roles)

        self.validate_self()

    def request_deletion(
        self,
        actor: Actor,
    ):
        self.deletion_requested_at = datetime.datetime.utcnow()

        event = UserDeletionRequested(
            actor=actor,
            id=self.id,
        )
        self.domain_events.append(event)

    def cancel_deletion(
        self,
        actor: Actor,
    ):
        self.deletion_requested_at = None

        event = UserDeletionCancelled(
            actor=actor,
            id=self.id,
        )
        self.domain_events.append(event)

    def accept_tos(self, actor: Actor):
        self.tos_accepted_at = datetime.datetime.utcnow()

    def delete(self, actor: Actor):
        pass
