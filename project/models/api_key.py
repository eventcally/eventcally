from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.extensions import db
from project.models.api_key_generated import ApiKeyGeneratedMixin


class ApiKey(db.Model, ApiKeyGeneratedMixin):
    __default_rate_limit_value__ = "500/hour"

    @property
    def owner(self):  # pragma: no cover
        if self.user:
            return self.user

        if self.admin_unit:
            return self.admin_unit

        if self.user_id:
            from project.models.user import User

            return User.query.get(self.user_id)

        if self.admin_unit_id:
            from project.models.admin_unit import AdminUnit

            return AdminUnit.query.get(self.admin_unit_id)

    def generate_key(self) -> str:
        from project.utils import generate_api_key, hash_api_key

        key = generate_api_key()
        self.key_hash = hash_api_key(key)
        return key

    @classmethod
    def from_aggregate(cls, aggregate: ApiKeyAggregate) -> ApiKey:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: ApiKeyAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.name = aggregate.name
        self.key_hash = aggregate.key_hash
        self.user_id = aggregate.user_id
        self.admin_unit_id = aggregate.admin_unit_id

    @classmethod
    def to_aggregate(cls, model: Optional[ApiKey]) -> Optional[ApiKeyAggregate]:
        if model is None:  # pragma: no cover
            return None

        return ApiKeyAggregate(
            id=model.id,
            name=model.name,
            key_hash=model.key_hash,
            user_id=model.user_id,
            admin_unit_id=model.admin_unit_id,
        )
