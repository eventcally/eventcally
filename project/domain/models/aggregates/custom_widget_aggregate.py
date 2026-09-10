from __future__ import annotations

from typing import Any, Dict, Optional

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class CustomWidgetAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    widget_type: str
    name: str
    settings: Optional[Dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        widget_type: str,
        name: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> CustomWidgetAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            widget_type=widget_type,
            name=name,
            settings=settings,
        )

        return instance

    def update(
        self,
        actor: Actor,
        widget_type: Unsetable[str] = unset,
        name: Unsetable[str] = unset,
        settings: NullableUnsetable[Dict[str, Any]] = unset,
    ):
        self._update_field_with_value("widget_type", widget_type)
        self._update_field_with_value("name", name)
        self._update_field_with_value("settings", settings)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
