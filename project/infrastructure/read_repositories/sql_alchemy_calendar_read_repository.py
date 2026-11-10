from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload, undefer_group

from project.application.queries.list_calendars_query import (
    CalendarSort,
    ListCalendarsQuery,
)
from project.application.read_models.calendar_read_models import (
    CalendarListItemReadModel,
    CalendarReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, Calendar, CalendarEntry
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
)
from project.shared.utils import parse_like_term

_number_of_events = (
    select(func.count())
    .where(CalendarEntry.calendar_id == Calendar.id)
    .scalar_subquery()
)

# "name" adds nothing: every ordering ends with lower(name), id.
_SORT_ORDER = {
    None: [],
    CalendarSort.name: [],
    CalendarSort.created_at_desc: [Calendar.created_at.desc()],
    CalendarSort.updated_at_desc: [Calendar.updated_at.desc().nulls_last()],
    CalendarSort.last_modified_at_desc: [Calendar.last_modified_at.desc()],
    CalendarSort.number_of_events_desc: [_number_of_events.desc()],
}


class SqlAlchemyCalendarReadRepository(AbstractCalendarReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: ListCalendarsQuery, include_private: bool
    ) -> Page[CalendarListItemReadModel]:
        filters = [
            Calendar.admin_unit_id == query.admin_unit_id,
            *trackable_filters(Calendar, query.trackable),
        ]
        if not include_private:
            filters.append(Calendar.private.is_(False))

        order_by = list(_SORT_ORDER[query.sort])

        if query.name:
            filters.append(Calendar.name.ilike(f"%{query.name}%"))
            order_by.append(Calendar.name.ilike(f"{query.name}%").desc())

        if query.keyword:
            filters.append(Calendar.name.ilike(parse_like_term(query.keyword)))

        order_by.extend([func.lower(Calendar.name), Calendar.id])

        stmt = (
            select(Calendar, _number_of_events.label("number_of_events"))
            .where(*filters)
            .options(undefer_group("trackable"))
            .order_by(*order_by)
        )
        count_stmt = select(Calendar.id).where(*filters)

        return paginate(self.session, stmt, count_stmt, query.page, _to_list_item)

    def get(self, object_id: ObjectId) -> Optional[CalendarReadModel]:
        stmt = (
            select(Calendar)
            .where(Calendar.id == object_id)
            .options(
                undefer_group("trackable"),
                joinedload(Calendar.admin_unit).load_only(AdminUnit.id, AdminUnit.name),
            )
        )
        calendar = self.session.execute(stmt).scalar_one_or_none()

        if calendar is None:
            return None

        return CalendarReadModel(
            id=calendar.id,
            admin_unit_id=calendar.admin_unit_id,
            admin_unit=OrganizationRefReadModel(
                id=calendar.admin_unit.id, name=calendar.admin_unit.name
            ),
            name=calendar.name,
            description=calendar.description,
            private=calendar.private,
            created_at=calendar.created_at,
            updated_at=calendar.updated_at,
        )

    def is_name_taken(
        self,
        admin_unit_id: ObjectId,
        name: str,
        exclude_id: Optional[ObjectId] = None,
    ) -> bool:
        filters = [
            Calendar.admin_unit_id == admin_unit_id,
            func.lower(Calendar.name) == name.lower(),
        ]

        if exclude_id is not None:
            filters.append(Calendar.id != exclude_id)

        return self.session.execute(select(exists().where(*filters))).scalar_one()


def _to_list_item(row) -> CalendarListItemReadModel:
    calendar, number_of_events = row

    return CalendarListItemReadModel(
        id=calendar.id,
        name=calendar.name,
        description=calendar.description,
        private=calendar.private,
        number_of_events=number_of_events,
        created_at=calendar.created_at,
        updated_at=calendar.updated_at,
        last_modified_at=calendar.last_modified_at,
    )
