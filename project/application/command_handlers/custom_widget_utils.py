from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)


def ensure_custom_widget_exists(
    custom_widget_id: int, uow: AbstractUnitOfWork
) -> CustomWidgetAggregate:
    custom_widget = uow.custom_widgets.get(custom_widget_id)

    if not custom_widget:  # pragma: no cover
        raise NotFoundError(f"Custom widget with id {custom_widget_id} not found")

    return custom_widget
