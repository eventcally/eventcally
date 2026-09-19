from __future__ import annotations

from typing import List, Optional

from project.domain import events
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import Unsetable


class AdminUnitMemberInvitationAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    email: Optional[str] = None
    roles: List[str] = []

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        email: str,
        roles: List[str] = [],
    ) -> AdminUnitMemberInvitationAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            email=email,
            roles=list(roles),
        )

        event = events.MemberInvitationCreated(
            actor=actor,
            id=-1,
            admin_unit_id=admin_unit_id,
            email=email,
        )
        instance.domain_events.append(event)

        return instance

    def update(
        self,
        actor: Actor,
        roles: Unsetable[List[str]] = unset,
    ):
        self._update_field_with_value("roles", roles)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
