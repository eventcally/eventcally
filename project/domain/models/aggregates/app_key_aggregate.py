from __future__ import annotations

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class AppKeyAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    app_id: ObjectId
    checksum: str
    kid: str
    public_key: str

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        app_id: ObjectId,
        checksum: str,
        kid: str,
        public_key: str,
    ) -> AppKeyAggregate:
        return cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            app_id=app_id,
            checksum=checksum,
            kid=kid,
            public_key=public_key,
        )

    def delete(self, actor: Actor):
        pass
