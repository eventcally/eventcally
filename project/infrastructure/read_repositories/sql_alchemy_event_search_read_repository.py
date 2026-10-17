import datetime
from typing import List, Optional

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql import extract

from project.application.queries.event_search_criteria import (
    EventSearchCriteria,
    EventSearchSort,
)
from project.application.queries.list_event_dates_query import ListEventDatesQuery
from project.application.queries.list_events_query import ListEventsQuery
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import TrackableSort
from project.application.read_models.event_read_models import (
    EventDateListItemReadModel,
    EventDateSearchHitReadModel,
    EventListItemReadModel,
    EventSearchItemReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_search_read_repository import (
    AbstractEventSearchReadRepository,
)
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.types.object_id import ObjectId
from project.infrastructure.read_repositories.event_read_model_mappers import (
    event_counts,
    event_load_options,
    reference_ids,
    to_event_search_item,
    verified_admin_units,
)
from project.infrastructure.read_repositories.query_helpers import (
    count,
    paginate,
    trackable_filters,
    trackable_order,
)
from project.models import (
    AdminUnit,
    CustomEventCategory,
    Event,
    EventCategory,
    EventDate,
    EventOrganizer,
    EventPlace,
    EventReference,
    Location,
)
from project.utils import parse_like_term

_LOAD_CHUNK = 200

_TRACKABLE_SORT = {
    EventSearchSort.created_at_desc: TrackableSort.created_at_desc,
    EventSearchSort.updated_at_desc: TrackableSort.updated_at_desc,
    EventSearchSort.last_modified_at_desc: TrackableSort.last_modified_at_desc,
}


class SqlAlchemyEventSearchReadRepository(AbstractEventSearchReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    # ---- searches -------------------------------------------------------------

    def search_event_dates(
        self,
        criteria: EventSearchCriteria,
        page_request: PageRequest,
        can_read_private_events: bool,
        can_read_planned_events: bool,
        reference_admin_unit_id: Optional[ObjectId],
    ) -> Page[EventDateSearchHitReadModel]:
        reference = _admin_unit_reference(criteria)
        filters = _event_filters(
            criteria, can_read_private_events, can_read_planned_events, reference
        )
        filters.append(_date_range_filter(criteria))
        stmt = _search_joins(select(EventDate.id), reference).where(*filters)
        order_by = [*_search_order(criteria, reference), EventDate.start, EventDate.id]

        date_ids = [
            row[0]
            for row in self.session.execute(
                stmt.order_by(*order_by)
                .limit(page_request.per_page)
                .offset(page_request.offset)
            )
        ]
        total = count(self.session, stmt)

        dates = {
            date.id: date
            for date in self.session.execute(
                select(EventDate).where(EventDate.id.in_(date_ids))
            )
            .scalars()
            .all()
        }
        events = self._load_events({date.event_id for date in dates.values()})
        items = self._to_items(events, reference_admin_unit_id)

        return Page[EventDateSearchHitReadModel](
            items=[
                EventDateSearchHitReadModel(
                    id=dates[date_id].id,
                    start=dates[date_id].start,
                    end=dates[date_id].end,
                    allday=dates[date_id].allday,
                    event=items[dates[date_id].event_id],
                )
                for date_id in date_ids
            ],
            page=page_request.page,
            per_page=page_request.per_page,
            total=total,
        )

    def search_events(
        self,
        criteria: EventSearchCriteria,
        page_request: PageRequest,
        can_read_private_events: bool,
        can_read_planned_events: bool,
        reference_admin_unit_id: Optional[ObjectId],
        include_counts: bool = False,
    ) -> Page[EventSearchItemReadModel]:
        reference = _admin_unit_reference(criteria)
        filters = _event_filters(
            criteria, can_read_private_events, can_read_planned_events, reference
        )
        filters.append(Event.dates.any(_date_range_filter(criteria)))
        stmt = _search_joins(select(Event.id), reference, from_event=True).where(
            *filters
        )
        order_by = [*_search_order(criteria, reference), Event.min_start, Event.id]

        event_ids = [
            row[0]
            for row in self.session.execute(
                stmt.order_by(*order_by)
                .limit(page_request.per_page)
                .offset(page_request.offset)
            )
        ]
        total = count(self.session, stmt)
        items = self._to_items(
            self._load_events(set(event_ids)), reference_admin_unit_id, include_counts
        )

        return Page[EventSearchItemReadModel](
            items=[items[event_id] for event_id in event_ids],
            page=page_request.page,
            per_page=page_request.per_page,
            total=total,
        )

    def list_events_for_search(
        self,
        criteria: EventSearchCriteria,
        can_read_private_events: bool,
        can_read_planned_events: bool,
    ) -> List[EventSearchItemReadModel]:
        reference = _admin_unit_reference(criteria)
        filters = _event_filters(
            criteria, can_read_private_events, can_read_planned_events, reference
        )
        filters.append(Event.dates.any(_date_range_filter(criteria)))
        stmt = _search_joins(select(Event.id), reference, from_event=True).where(
            *filters
        )
        order_by = [*_search_order(criteria, reference), Event.min_start, Event.id]
        event_ids = [row[0] for row in self.session.execute(stmt.order_by(*order_by))]
        items = {}

        for start in range(0, len(event_ids), _LOAD_CHUNK):
            chunk = event_ids[start : start + _LOAD_CHUNK]
            items.update(self._to_items(self._load_events(set(chunk)), None))

        return [items[event_id] for event_id in event_ids]

    def _load_events(self, event_ids: set) -> dict:
        if not event_ids:
            return {}

        events = (
            self.session.execute(
                select(Event)
                .where(Event.id.in_(event_ids))
                .options(*event_load_options())
            )
            .scalars()
            .all()
        )
        return {event.id: event for event in events}

    def _to_items(
        self, events: dict, reference_admin_unit_id, include_counts: bool = False
    ) -> dict:
        verified = verified_admin_units(
            self.session, {event.admin_unit_id for event in events.values()}
        )
        references = reference_ids(self.session, events, reference_admin_unit_id)
        counts = event_counts(self.session, events) if include_counts else {}

        return {
            event_id: to_event_search_item(
                event,
                verified.get(event.admin_unit_id, False),
                references.get(event_id),
                counts.get(event_id),
            )
            for event_id, event in events.items()
        }

    # ---- lists ----------------------------------------------------------------

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list_events(
        self, query: ListEventsQuery, can_read_private_events: bool
    ) -> Page[EventListItemReadModel]:
        filters = [*trackable_filters(Event, query.trackable)]
        stmt = select(Event.id, Event.name, Event.created_at, Event.updated_at)

        if query.admin_unit_id is not None:
            filters.append(Event.admin_unit_id == query.admin_unit_id)

        if not can_read_private_events or query.admin_unit_id is None:
            stmt = stmt.join(Event.admin_unit)
            filters.extend(
                [
                    Event.public_status == EventPublicStatus.published,
                    AdminUnit.is_verified,
                ]
            )

        stmt = stmt.where(*filters).order_by(
            *trackable_order(Event, query.sort), Event.min_start, Event.id
        )
        count_stmt = select(Event.id).where(*filters)

        if not can_read_private_events or query.admin_unit_id is None:
            count_stmt = count_stmt.join(Event.admin_unit)

        return paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: EventListItemReadModel(
                id=row.id,
                name=row.name,
                created_at=row.created_at,
                updated_at=row.updated_at,
            ),
        )

    def list_event_dates(
        self, query: ListEventDatesQuery
    ) -> Page[EventDateListItemReadModel]:
        filters = [
            Event.public_status == EventPublicStatus.published,
            AdminUnit.is_verified,
            *trackable_filters(Event, query.trackable),
        ]
        joined = (
            select(EventDate.id, EventDate.start)
            .join(EventDate.event)
            .join(Event.admin_unit)
            .where(*filters)
        )
        stmt = joined.order_by(
            *trackable_order(Event, query.sort), EventDate.start, EventDate.id
        )
        count_stmt = (
            select(EventDate.id)
            .join(EventDate.event)
            .join(Event.admin_unit)
            .where(*filters)
        )

        return paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: EventDateListItemReadModel(id=row.id, start=row.start),
        )


def _admin_unit_reference(criteria: EventSearchCriteria):
    """The references the filtered organization holds, outer-joined by event."""
    if not criteria.admin_unit_id:
        return None

    if not (
        criteria.include_admin_unit_references or criteria.admin_unit_references_only
    ):
        return None

    subquery = (
        select(EventReference)
        .where(EventReference.admin_unit_id == criteria.admin_unit_id)
        .subquery()
    )
    return aliased(EventReference, subquery)


def _search_joins(stmt, reference, from_event: bool = False):
    if from_event:
        stmt = stmt.select_from(Event).join(Event.admin_unit)
    else:
        stmt = stmt.join(EventDate.event).join(Event.admin_unit)

    stmt = (
        stmt.join(Event.event_place, isouter=True)
        .join(EventPlace.location, isouter=True)
        .join(Event.organizer, isouter=True)
    )

    if reference is not None:
        stmt = stmt.join(reference, Event.id == reference.event_id, isouter=True)

    return stmt


def _search_order(criteria: EventSearchCriteria, reference) -> list:
    sort = criteria.sort

    if sort in _TRACKABLE_SORT:
        return trackable_order(Event, _TRACKABLE_SORT[sort])

    if sort == EventSearchSort.rating_desc:
        if reference is not None:
            return [
                case(
                    (reference.rating.isnot(None), reference.rating),
                    else_=Event.rating,
                ).desc()
            ]

        return [Event.rating.desc()]

    if sort == EventSearchSort.reference_created_at_desc and reference is not None:
        return [reference.created_at.desc()]

    return []


def _event_filters(
    criteria: EventSearchCriteria,
    can_read_private_events: bool,
    can_read_planned_events: bool,
    reference,
) -> list:
    filters = [*trackable_filters(Event, criteria.trackable)]

    if criteria.keyword:
        tq = func.websearch_to_tsquery("german", criteria.keyword)
        like_keyword = "%" + criteria.keyword + "%"
        filters.append(
            or_(
                Event.__ts_vector__.op("@@")(tq),
                Event.name.ilike(like_keyword),
                EventPlace.name.ilike(like_keyword),
                Location.city.ilike(like_keyword),
                EventOrganizer.name.ilike(like_keyword),
            )
        )

    if criteria.category_ids:
        filters.append(
            Event.categories.any(EventCategory.id.in_(criteria.category_ids))
        )

    if criteria.custom_category_set_ids:
        filters.append(
            Event.custom_categories.any(
                CustomEventCategory.category_set_id.in_(
                    criteria.custom_category_set_ids
                )
            )
        )

    if criteria.status:
        filters.append(Event.status.in_(criteria.status))

    filters.append(
        Event.public_status.in_(
            _public_statuses(criteria, can_read_private_events, can_read_planned_events)
        )
    )

    if not can_read_private_events or not criteria.admin_unit_id:
        filters.append(AdminUnit.is_verified)

    if criteria.organizer_id:
        filters.append(Event.organizer_id == criteria.organizer_id)

    if criteria.event_place_id:
        filters.append(Event.event_place_id == criteria.event_place_id)

    if criteria.latitude and criteria.longitude and criteria.distance:
        point = "POINT({} {})".format(criteria.longitude, criteria.latitude)
        filters.append(
            func.ST_DistanceSphere(Location.coordinate, point) <= criteria.distance
        )

    if criteria.postal_codes:
        filters.append(
            or_(
                *[
                    Location.postalCode.ilike(code + "%")
                    for code in criteria.postal_codes
                ]
            )
        )

    filters.extend(_tag_filters(Event.tags, criteria.tags))

    if (
        can_read_private_events
        and criteria.admin_unit_id
        and not criteria.include_admin_unit_references
    ):
        filters.extend(_tag_filters(Event.internal_tags, criteria.internal_tags))

    if criteria.not_referenced_by_admin_unit_id:
        filters.append(Event.admin_unit_id != criteria.not_referenced_by_admin_unit_id)
        filters.append(
            ~exists().where(
                EventReference.event_id == Event.id,
                EventReference.admin_unit_id
                == criteria.not_referenced_by_admin_unit_id,
            )
        )

    if criteria.exclude_recurring:
        filters.append(~Event.is_recurring)

    if criteria.is_recurring is not None:
        filters.append(
            Event.is_recurring if criteria.is_recurring else ~Event.is_recurring
        )

    if criteria.name:
        filters.append(Event.name.ilike(parse_like_term(criteria.name)))

    if criteria.expected_participants_min:
        filters.append(
            Event.expected_participants >= criteria.expected_participants_min
        )

    if criteria.admin_unit_id:
        if reference is not None:
            if criteria.admin_unit_references_only:
                filters.append(reference.id.isnot(None))
            else:
                filters.append(
                    or_(
                        Event.admin_unit_id == criteria.admin_unit_id,
                        reference.id.isnot(None),
                    )
                )
        else:
            filters.append(Event.admin_unit_id == criteria.admin_unit_id)

    return filters


def _public_statuses(
    criteria: EventSearchCriteria,
    can_read_private_events: bool,
    can_read_planned_events: bool,
) -> list:
    if criteria.public_status:
        statuses = list(criteria.public_status)
    elif can_read_private_events:
        statuses = [
            EventPublicStatus.published,
            EventPublicStatus.planned,
            EventPublicStatus.draft,
        ]
    else:
        statuses = [EventPublicStatus.published, EventPublicStatus.draft]

    if not can_read_private_events and EventPublicStatus.draft in statuses:
        statuses.remove(EventPublicStatus.draft)

    if (
        not can_read_private_events
        and not can_read_planned_events
        and EventPublicStatus.planned in statuses
    ):
        statuses.remove(EventPublicStatus.planned)

    return statuses


def _tag_filters(column, tags: list) -> list:
    if not tags:
        return []

    return [(func.string_to_array(column, ",")).op("@>")(tags)]


def _date_range_filter(criteria: EventSearchCriteria):
    date_filter = EventDate.start >= datetime.datetime.min

    if criteria.date_from:
        date_filter = or_(
            EventDate.start >= criteria.date_from,
            and_(EventDate.end.isnot(None), EventDate.end >= criteria.date_from),
        )

    if criteria.date_to:
        date_to_filter = or_(
            EventDate.start < criteria.date_to,
            and_(EventDate.end.isnot(None), EventDate.end < criteria.date_to),
        )
        date_filter = and_(date_filter, date_to_filter)

    # PostgreSQL specific https://stackoverflow.com/a/25597632
    if criteria.weekdays:
        date_filter = and_(
            date_filter, extract("dow", EventDate.start).in_(criteria.weekdays)
        )

    return date_filter
