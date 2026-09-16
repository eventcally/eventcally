from __future__ import annotations

from typing import List

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import Unsetable


class OrganisationMemberAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    user_id: ObjectId
    roles: List[str] = []

    @classmethod
    def create(
        cls, admin_unit_id: ObjectId, user_id: ObjectId, roles: List[str] = []
    ) -> OrganisationMemberAggregate:
        return cls(
            id=-1, admin_unit_id=admin_unit_id, user_id=user_id, roles=list(roles)
        )

    def add_roles(self, role_names: List[str]):
        self.roles = self.roles + [r for r in role_names if r not in self.roles]

    def update(self, actor: Actor, roles: Unsetable[List[str]] = unset):
        self._update_field_with_value("roles", roles)
        self.validate_self()
