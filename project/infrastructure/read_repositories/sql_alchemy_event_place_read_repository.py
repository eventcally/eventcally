from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import contains_eager, joinedload, undefer, undefer_group

from project.application.queries.list_event_places_query import (
    EventPlaceSort,
    ListEventPlacesQuery,
)
from project.application.queries.lookup_event_places_query import LookupEventPlacesQuery
from project.application.read_models.event_place_read_models import (
    EventPlaceDetailReadModel,
    EventPlaceEditReadModel,
    EventPlaceListItemReadModel,
    EventPlaceSuggestionReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, Event, EventPlace, Image, Location
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    to_image_edit_read_model,
    to_image_read_model,
    to_location_read_model,
)
from project.shared.utils import parse_like_term

_number_of_events = (
    select(func.count()).where(Event.event_place_id == EventPlace.id).scalar_subquery()
)

# "name" adds nothing: every ordering ends with lower(name), id.
_SORT_ORDER = {
    None: [],
    EventPlaceSort.name: [],
    EventPlaceSort.created_at_desc: [EventPlace.created_at.desc()],
    EventPlaceSort.updated_at_desc: [EventPlace.updated_at.desc().nulls_last()],
    EventPlaceSort.last_modified_at_desc: [EventPlace.last_modified_at.desc()],
    EventPlaceSort.number_of_events_desc: [_number_of_events.desc()],
}


class SqlAlchemyEventPlaceReadRepository(AbstractEventPlaceReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(self, query: ListEventPlacesQuery) -> Page[EventPlaceListItemReadModel]:
        filters = [
            EventPlace.admin_unit_id == query.admin_unit_id,
            *trackable_filters(EventPlace, query.trackable),
        ]

        if query.name:
            filters.append(EventPlace.name.ilike(f"%{query.name}%"))

        if query.keyword:
            filters.append(EventPlace.name.ilike(parse_like_term(query.keyword)))

        order_by = [
            *_SORT_ORDER[query.sort],
            func.lower(EventPlace.name),
            EventPlace.id,
        ]

        stmt = (
            select(
                EventPlace,
                _number_of_events.label("number_of_events"),
                EventPlace.photo_id.is_not(None).label("has_photo"),
                Location.coordinate.is_not(None).label("has_coordinates"),
            )
            .outerjoin(EventPlace.location)
            .where(*filters)
            .options(
                undefer_group("trackable"),
                contains_eager(EventPlace.location),
            )
            .order_by(*order_by)
        )
        count_stmt = select(EventPlace.id).where(*filters)

        return paginate(self.session, stmt, count_stmt, query.page, _to_list_item)

    def lookup(
        self, query: LookupEventPlacesQuery
    ) -> Page[EventPlaceSuggestionReadModel]:
        filters = [EventPlace.admin_unit_id == query.admin_unit_id]

        if query.term:
            filters.append(EventPlace.name.ilike(parse_like_term(query.term)))

        stmt = (
            select(EventPlace)
            .where(*filters)
            .options(joinedload(EventPlace.location))
            .order_by(func.lower(EventPlace.name), EventPlace.id)
        )
        count_stmt = select(EventPlace.id).where(*filters)

        return paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: _to_suggestion(row[0]),
        )

    def get_ref(
        self, admin_unit_id: ObjectId, object_id: ObjectId
    ) -> Optional[EventPlaceSuggestionReadModel]:
        place = self.session.execute(
            select(EventPlace)
            .where(
                EventPlace.id == object_id,
                EventPlace.admin_unit_id == admin_unit_id,
            )
            .options(joinedload(EventPlace.location))
        ).scalar_one_or_none()

        return _to_suggestion(place) if place else None

    def get(self, object_id: ObjectId) -> Optional[EventPlaceDetailReadModel]:
        stmt = (
            select(EventPlace)
            .where(EventPlace.id == object_id)
            .options(
                undefer_group("trackable"),
                joinedload(EventPlace.location),
                joinedload(EventPlace.photo).options(
                    undefer(Image.created_at),
                    undefer(Image.updated_at),
                    joinedload(Image.license),
                ),
                joinedload(EventPlace.admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                ),
            )
        )
        place = self.session.execute(stmt).scalar_one_or_none()

        if place is None:
            return None

        return _to_detail(place)

    def get_for_edit(self, object_id: ObjectId) -> Optional[EventPlaceEditReadModel]:
        stmt = (
            select(EventPlace)
            .where(EventPlace.id == object_id)
            .options(
                joinedload(EventPlace.location),
                joinedload(EventPlace.photo).options(
                    undefer(Image.data),
                    joinedload(Image.license),
                ),
            )
        )
        place = self.session.execute(stmt).scalar_one_or_none()

        if place is None:
            return None

        return _to_edit(place)

    def is_name_taken(
        self,
        admin_unit_id: ObjectId,
        name: str,
        exclude_id: Optional[ObjectId] = None,
    ) -> bool:
        filters = [
            EventPlace.admin_unit_id == admin_unit_id,
            func.lower(EventPlace.name) == name.lower(),
        ]

        if exclude_id is not None:
            filters.append(EventPlace.id != exclude_id)

        return self.session.execute(select(exists().where(*filters))).scalar_one()


def _to_list_item(row) -> EventPlaceListItemReadModel:
    place, number_of_events, has_photo, has_coordinates = row

    return EventPlaceListItemReadModel(
        id=place.id,
        name=place.name,
        location=to_location_read_model(place.location),
        has_coordinates=has_coordinates,
        has_photo=has_photo,
        number_of_events=number_of_events,
        created_at=place.created_at,
        updated_at=place.updated_at,
        last_modified_at=place.last_modified_at,
    )


def _to_detail(place) -> EventPlaceDetailReadModel:
    return EventPlaceDetailReadModel(
        id=place.id,
        name=place.name,
        url=place.url,
        description=place.description,
        created_at=place.created_at,
        updated_at=place.updated_at,
        location=to_location_read_model(place.location),
        photo=to_image_read_model(place.photo),
        admin_unit=OrganizationRefReadModel(
            id=place.admin_unit.id, name=place.admin_unit.name
        ),
    )


def _to_suggestion(place) -> EventPlaceSuggestionReadModel:
    return EventPlaceSuggestionReadModel(
        id=place.id,
        name=place.name,
        location=to_location_read_model(place.location),
    )


def _to_edit(place) -> EventPlaceEditReadModel:
    return EventPlaceEditReadModel(
        id=place.id,
        admin_unit_id=place.admin_unit_id,
        name=place.name,
        url=place.url,
        description=place.description,
        location=to_location_read_model(place.location),
        photo=to_image_edit_read_model(place.photo),
    )
