from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload, undefer, undefer_group

from project.application.queries.list_event_organizers_query import (
    EventOrganizerSort,
    ListEventOrganizersQuery,
)
from project.application.queries.lookup_event_organizers_query import (
    LookupEventOrganizersQuery,
)
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerDetailReadModel,
    EventOrganizerEditReadModel,
    EventOrganizerListItemReadModel,
    EventOrganizerRefReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_organizer_read_repository import (
    AbstractEventOrganizerReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, Event, EventOrganizer, Image
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    to_image_edit_read_model,
    to_image_read_model,
    to_location_read_model,
)
from project.utils import parse_like_term

_number_of_events = (
    select(func.count())
    .where(Event.organizer_id == EventOrganizer.id)
    .scalar_subquery()
)

# "name" adds nothing: every ordering ends with lower(name), id.
_SORT_ORDER = {
    None: [],
    EventOrganizerSort.name: [],
    EventOrganizerSort.created_at_desc: [EventOrganizer.created_at.desc()],
    EventOrganizerSort.updated_at_desc: [EventOrganizer.updated_at.desc().nulls_last()],
    EventOrganizerSort.last_modified_at_desc: [EventOrganizer.last_modified_at.desc()],
    EventOrganizerSort.number_of_events_desc: [_number_of_events.desc()],
}


class SqlAlchemyEventOrganizerReadRepository(AbstractEventOrganizerReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: ListEventOrganizersQuery
    ) -> Page[EventOrganizerListItemReadModel]:
        filters = [
            EventOrganizer.admin_unit_id == query.admin_unit_id,
            *trackable_filters(EventOrganizer, query.trackable),
        ]
        order_by = list(_SORT_ORDER[query.sort])

        if query.name:
            filters.append(EventOrganizer.name.ilike(f"%{query.name}%"))
            order_by.append(EventOrganizer.name.ilike(f"{query.name}%").desc())

        if query.keyword:
            filters.append(EventOrganizer.name.ilike(parse_like_term(query.keyword)))

        order_by.extend([func.lower(EventOrganizer.name), EventOrganizer.id])

        stmt = (
            select(
                EventOrganizer,
                _number_of_events.label("number_of_events"),
                EventOrganizer.logo_id.is_not(None).label("has_logo"),
            )
            .where(*filters)
            .options(
                undefer_group("detail"),
                undefer_group("trackable"),
                joinedload(EventOrganizer.location),
            )
            .order_by(*order_by)
        )
        count_stmt = select(EventOrganizer.id).where(*filters)

        return paginate(self.session, stmt, count_stmt, query.page, _to_list_item)

    def lookup(
        self, query: LookupEventOrganizersQuery
    ) -> Page[EventOrganizerRefReadModel]:
        filters = [EventOrganizer.admin_unit_id == query.admin_unit_id]

        if query.term:
            filters.append(EventOrganizer.name.ilike(parse_like_term(query.term)))

        stmt = (
            select(EventOrganizer.id, EventOrganizer.name)
            .where(*filters)
            .order_by(func.lower(EventOrganizer.name), EventOrganizer.id)
        )
        count_stmt = select(EventOrganizer.id).where(*filters)

        return paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: EventOrganizerRefReadModel(id=row.id, name=row.name),
        )

    def get_ref(
        self, admin_unit_id: ObjectId, object_id: ObjectId
    ) -> Optional[EventOrganizerRefReadModel]:
        row = self.session.execute(
            select(EventOrganizer.id, EventOrganizer.name).where(
                EventOrganizer.id == object_id,
                EventOrganizer.admin_unit_id == admin_unit_id,
            )
        ).one_or_none()

        if row is None:
            return None

        return EventOrganizerRefReadModel(id=row.id, name=row.name)

    def get(self, object_id: ObjectId) -> Optional[EventOrganizerDetailReadModel]:
        stmt = (
            select(EventOrganizer)
            .where(EventOrganizer.id == object_id)
            .options(
                undefer_group("detail"),
                undefer_group("trackable"),
                joinedload(EventOrganizer.location),
                joinedload(EventOrganizer.logo).options(
                    undefer(Image.created_at),
                    undefer(Image.updated_at),
                    joinedload(Image.license),
                ),
                joinedload(EventOrganizer.admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                ),
            )
        )
        organizer = self.session.execute(stmt).scalar_one_or_none()

        if organizer is None:
            return None

        return _to_detail(organizer)

    def get_for_edit(
        self, object_id: ObjectId
    ) -> Optional[EventOrganizerEditReadModel]:
        stmt = (
            select(EventOrganizer)
            .where(EventOrganizer.id == object_id)
            .options(
                undefer_group("detail"),
                joinedload(EventOrganizer.location),
                joinedload(EventOrganizer.logo).options(
                    undefer(Image.data),
                    joinedload(Image.license),
                ),
            )
        )
        organizer = self.session.execute(stmt).scalar_one_or_none()

        if organizer is None:
            return None

        return _to_edit(organizer)

    def is_name_taken(
        self,
        admin_unit_id: ObjectId,
        name: str,
        exclude_id: Optional[ObjectId] = None,
    ) -> bool:
        filters = [
            EventOrganizer.admin_unit_id == admin_unit_id,
            func.lower(EventOrganizer.name) == name.lower(),
        ]

        if exclude_id is not None:
            filters.append(EventOrganizer.id != exclude_id)

        return self.session.execute(select(exists().where(*filters))).scalar_one()


def _to_list_item(row) -> EventOrganizerListItemReadModel:
    organizer, number_of_events, has_logo = row

    return EventOrganizerListItemReadModel(
        id=organizer.id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        location=to_location_read_model(organizer.location),
        has_logo=has_logo,
        number_of_events=number_of_events,
        created_at=organizer.created_at,
        updated_at=organizer.updated_at,
        last_modified_at=organizer.last_modified_at,
    )


def _to_detail(organizer) -> EventOrganizerDetailReadModel:
    return EventOrganizerDetailReadModel(
        id=organizer.id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        created_at=organizer.created_at,
        updated_at=organizer.updated_at,
        location=to_location_read_model(organizer.location),
        logo=to_image_read_model(organizer.logo),
        admin_unit=OrganizationRefReadModel(
            id=organizer.admin_unit.id, name=organizer.admin_unit.name
        ),
    )


def _to_edit(organizer) -> EventOrganizerEditReadModel:
    return EventOrganizerEditReadModel(
        id=organizer.id,
        admin_unit_id=organizer.admin_unit_id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        location=to_location_read_model(organizer.location),
        logo=to_image_edit_read_model(organizer.logo),
    )
