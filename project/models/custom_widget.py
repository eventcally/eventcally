from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)
from project.extensions import db
from project.models.custom_widget_generated import CustomWidgetGeneratedMixin


class CustomWidget(db.Model, CustomWidgetGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: CustomWidgetAggregate) -> CustomWidget:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: CustomWidgetAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.widget_type = aggregate.widget_type
        self.name = aggregate.name
        self.settings = aggregate.settings

    @classmethod
    def to_aggregate(
        cls, model: Optional[CustomWidget]
    ) -> Optional[CustomWidgetAggregate]:
        if model is None:  # pragma: no cover
            return None

        return CustomWidgetAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            widget_type=model.widget_type,
            name=model.name,
            settings=model.settings,
        )
