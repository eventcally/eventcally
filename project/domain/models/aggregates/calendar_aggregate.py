from __future__ import annotations

from typing import Optional

from pydantic import field_validator

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.text import TrimmedText
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class CalendarAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    name: TrimmedText
    description: Optional[str] = None
    private: bool = False

    @field_validator("name")
    @classmethod
    def _name_must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Name must not be empty")
        return value

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        name: str,
        description: Optional[str] = None,
        private: bool = False,
    ) -> CalendarAggregate:
        return cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            name=name,
            description=description,
            private=private,
        )

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
        description: NullableUnsetable[str] = unset,
        private: Unsetable[bool] = unset,
    ):
        self._update_field_with_value("name", name)
        self._update_field_with_value("description", description)
        self._update_field_with_value("private", private)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
