from __future__ import annotations

from typing import Optional

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class OAuth2TokenAggregate(BaseAggregate):
    id: ObjectId
    user_id: Optional[ObjectId] = None
    is_revoked: bool = False

    def revoke(self, actor: Actor):
        if self.is_revoked:
            raise ConstraintError("This OAuth2 token has already been revoked.")

        self.is_revoked = True
