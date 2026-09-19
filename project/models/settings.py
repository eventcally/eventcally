from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.settings_aggregate import SettingsAggregate
from project.extensions import db
from project.models.settings_generated import SettingsGeneratedMixin


class Settings(db.Model, SettingsGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: SettingsAggregate) -> Settings:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: SettingsAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.tos = aggregate.tos
        self.legal_notice = aggregate.legal_notice
        self.contact = aggregate.contact
        self.privacy = aggregate.privacy
        self.start_page = aggregate.start_page
        self.announcement = aggregate.announcement
        self.planning_external_calendars = aggregate.planning_external_calendars

    @classmethod
    def to_aggregate(cls, model: Optional[Settings]) -> Optional[SettingsAggregate]:
        if model is None:  # pragma: no cover
            return None

        return SettingsAggregate(
            id=model.id,
            tos=model.tos,
            legal_notice=model.legal_notice,
            contact=model.contact,
            privacy=model.privacy,
            start_page=model.start_page,
            announcement=model.announcement,
            planning_external_calendars=model.planning_external_calendars,
        )
