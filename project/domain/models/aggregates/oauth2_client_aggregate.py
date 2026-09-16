from __future__ import annotations

from typing import List, Optional

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class OAuth2ClientAggregate(BaseAggregate):
    id: ObjectId
    name: str
    redirect_uris: List[str] = []
    scope: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    user_id: Optional[ObjectId] = None
    admin_unit_id: Optional[ObjectId] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        name: str,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str] = [],
        scope: Optional[str] = None,
        user_id: Optional[ObjectId] = None,
        admin_unit_id: Optional[ObjectId] = None,
    ) -> OAuth2ClientAggregate:
        if (user_id is None) == (admin_unit_id is None):
            raise ConstraintError(
                "Exactly one of user_id or admin_unit_id must be set."
            )

        instance = cls(
            id=-1,
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=redirect_uris,
            scope=scope,
            user_id=user_id,
            admin_unit_id=admin_unit_id,
        )

        return instance

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
        redirect_uris: Unsetable[List[str]] = unset,
        scope: NullableUnsetable[str] = unset,
    ):
        self._update_field_with_value("name", name)
        self._update_field_with_value("redirect_uris", redirect_uris)
        self._update_field_with_value("scope", scope)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
