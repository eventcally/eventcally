from typing import Optional

from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)
from project.domain.repositories import AbstractCustomWidgetRepository
from project.models.custom_widget import CustomWidget


class SqlAlchemyCustomWidgetRepository(AbstractCustomWidgetRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, custom_widget: CustomWidgetAggregate):
        model = CustomWidget.from_aggregate(custom_widget)
        self.session.add(model)
        self.session.flush()

        custom_widget.id = model.id

    def _update(self, custom_widget: CustomWidgetAggregate):
        model = self._get_model(custom_widget.id)
        model.fill_from_aggregate(custom_widget)
        self.session.merge(model)
        self.session.flush()

    def _get_model(self, object_id: int) -> Optional[CustomWidget]:
        return self.session.query(CustomWidget).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[CustomWidgetAggregate]:
        model = self._get_model(object_id)
        return CustomWidget.to_aggregate(model) if model else None

    def _remove(self, custom_widget: CustomWidgetAggregate):
        model = self._get_model(custom_widget.id)
        self.session.delete(model)
