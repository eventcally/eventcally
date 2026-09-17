from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable


class SettingsAggregate(BaseAggregate):
    id: ObjectId
    tos: Optional[str] = None
    legal_notice: Optional[str] = None
    contact: Optional[str] = None
    privacy: Optional[str] = None
    start_page: Optional[str] = None
    announcement: Optional[str] = None
    planning_external_calendars: Optional[str] = None

    @classmethod
    def create(cls, actor: Actor) -> SettingsAggregate:
        return cls(id=-1)

    def update(
        self,
        actor: Actor,
        tos: NullableUnsetable[str] = unset,
        legal_notice: NullableUnsetable[str] = unset,
        contact: NullableUnsetable[str] = unset,
        privacy: NullableUnsetable[str] = unset,
        start_page: NullableUnsetable[str] = unset,
        announcement: NullableUnsetable[str] = unset,
        planning_external_calendars: NullableUnsetable[str] = unset,
    ):
        self._update_field_with_value("tos", tos)
        self._update_field_with_value("legal_notice", legal_notice)
        self._update_field_with_value("contact", contact)
        self._update_field_with_value("privacy", privacy)
        self._update_field_with_value("start_page", start_page)
        self._update_field_with_value("announcement", announcement)
        self._update_field_with_value(
            "planning_external_calendars", planning_external_calendars
        )

        self.validate_self()
