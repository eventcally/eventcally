from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload, undefer_group

from project.application.queries.list_custom_widgets_query import ListCustomWidgetsQuery
from project.application.read_models.custom_widget_read_models import (
    CustomWidgetReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_custom_widget_read_repository import (
    AbstractCustomWidgetReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.read_repositories.query_helpers import paginate
from project.infrastructure.read_repositories.read_model_mappers import (
    to_organization_ref_read_model,
)
from project.models import AdminUnit, CustomWidget

_options = [
    undefer_group("trackable"),
    joinedload(CustomWidget.admin_unit).load_only(AdminUnit.id, AdminUnit.name),
]


class SqlAlchemyCustomWidgetReadRepository(AbstractCustomWidgetReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(self, query: ListCustomWidgetsQuery) -> Page[CustomWidgetReadModel]:
        filters = [CustomWidget.admin_unit_id == query.admin_unit_id]

        if query.name:
            filters.append(CustomWidget.name.ilike("%" + query.name + "%"))

        stmt = (
            select(CustomWidget)
            .where(*filters)
            .options(*_options)
            .order_by(func.lower(CustomWidget.name), CustomWidget.id)
        )
        count_stmt = select(CustomWidget.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )

    def get(self, object_id: ObjectId) -> Optional[CustomWidgetReadModel]:
        widget = self.session.execute(
            select(CustomWidget).where(CustomWidget.id == object_id).options(*_options)
        ).scalar_one_or_none()
        return _to_model(widget) if widget else None


def _to_model(widget) -> CustomWidgetReadModel:
    return CustomWidgetReadModel(
        id=widget.id,
        admin_unit_id=widget.admin_unit_id,
        widget_type=widget.widget_type,
        name=widget.name,
        settings=widget.settings,
        created_at=widget.created_at,
        updated_at=widget.updated_at,
        admin_unit=to_organization_ref_read_model(widget.admin_unit),
    )
