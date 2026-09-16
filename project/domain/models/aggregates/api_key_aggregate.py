from __future__ import annotations

from typing import Optional

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import Unsetable


class ApiKeyAggregate(BaseAggregate):
    id: ObjectId
    name: str
    key_hash: str
    user_id: Optional[ObjectId] = None
    admin_unit_id: Optional[ObjectId] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        name: str,
        key_hash: str,
        user_id: Optional[ObjectId] = None,
        admin_unit_id: Optional[ObjectId] = None,
    ) -> ApiKeyAggregate:
        if (user_id is None) == (admin_unit_id is None):
            raise ConstraintError(
                "Exactly one of user_id or admin_unit_id must be set."
            )

        instance = cls(
            id=-1,
            name=name,
            key_hash=key_hash,
            user_id=user_id,
            admin_unit_id=admin_unit_id,
        )

        return instance

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
    ):
        self._update_field_with_value("name", name)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
