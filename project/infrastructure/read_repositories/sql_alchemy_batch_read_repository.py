import datetime
from typing import List

from sqlalchemy import or_, select
from sqlalchemy.orm import Load, joinedload

from project.application.queries.list_dump_event_references_query import (
    ListDumpEventReferencesQuery,
)
from project.application.queries.list_dump_events_query import ListDumpEventsQuery
from project.application.queries.list_dump_organizations_query import (
    ListDumpOrganizationsQuery,
)
from project.application.queries.list_dump_organizers_query import (
    ListDumpOrganizersQuery,
)
from project.application.queries.list_dump_places_query import ListDumpPlacesQuery
from project.application.read_models.batch_read_models import (
    DumpEventReferenceReadModel,
    DumpOrganizerReadModel,
    SitemapEventReadModel,
)
from project.application.read_models.event_read_models import (
    EventDetailReadModel,
    EventOrganizationReadModel,
    EventPlaceEmbedReadModel,
)
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)
from project.application.read_repositories.abstract_batch_read_repository import (
    AbstractBatchReadRepository,
)
from project.domain.models.deletion_policy import DELETION_GRACE_PERIOD
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    Event,
    EventCategory,
    EventDate,
    EventOrganizer,
    EventPlace,
    EventReference,
    User,
)
from project.infrastructure.read_repositories.event_read_model_mappers import (
    event_load_options,
    image_options,
    to_event_detail,
    to_organization_embed,
    to_organizer_embed,
    to_place_embed,
    verified_admin_units,
)
from project.shared.dateutils import get_today


class SqlAlchemyBatchReadRepository(AbstractBatchReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _batch(self, stmt, model, query):
        return (
            self.session.execute(
                stmt.where(model.id > query.after_id)
                .order_by(model.id)
                .limit(query.limit)
            )
            .scalars()
            .all()
        )

    def list_dump_events(
        self, query: ListDumpEventsQuery
    ) -> List[EventDetailReadModel]:
        stmt = select(Event).options(*event_load_options(co_organizers=True))

        if query.admin_unit_id is not None:
            stmt = stmt.where(Event.admin_unit_id == query.admin_unit_id)

        if query.public_only:
            stmt = stmt.join(Event.admin_unit).where(
                Event.public_status == EventPublicStatus.published,
                AdminUnit.is_verified,
            )

        events = self._batch(stmt, Event, query)
        verified = verified_admin_units(
            self.session, {event.admin_unit_id for event in events}
        )
        return [
            to_event_detail(event, verified.get(event.admin_unit_id, False))
            for event in events
        ]

    def list_dump_places(
        self, query: ListDumpPlacesQuery
    ) -> List[EventPlaceEmbedReadModel]:
        stmt = select(EventPlace).options(
            Load(EventPlace).undefer_group("trackable"),
            joinedload(EventPlace.location),
            *image_options(joinedload(EventPlace.photo)),
        )

        if query.admin_unit_id is not None:
            stmt = stmt.where(EventPlace.admin_unit_id == query.admin_unit_id)

        return [to_place_embed(p) for p in self._batch(stmt, EventPlace, query)]

    def list_dump_organizers(
        self, query: ListDumpOrganizersQuery
    ) -> List[DumpOrganizerReadModel]:
        stmt = select(EventOrganizer).options(
            Load(EventOrganizer).undefer_group("detail"),
            Load(EventOrganizer).undefer_group("trackable"),
            joinedload(EventOrganizer.location),
            *image_options(joinedload(EventOrganizer.logo)),
        )

        if query.admin_unit_id is not None:
            stmt = stmt.where(EventOrganizer.admin_unit_id == query.admin_unit_id)

        return [
            DumpOrganizerReadModel(
                **to_organizer_embed(o).model_dump(), admin_unit_id=o.admin_unit_id
            )
            for o in self._batch(stmt, EventOrganizer, query)
        ]

    def list_dump_organizations(
        self, query: ListDumpOrganizationsQuery
    ) -> List[EventOrganizationReadModel]:
        stmt = select(AdminUnit).options(
            Load(AdminUnit).undefer(AdminUnit.logo_id),
            Load(AdminUnit).undefer_group("detail"),
            Load(AdminUnit).undefer_group("trackable"),
            joinedload(AdminUnit.location),
            *image_options(joinedload(AdminUnit.logo)),
        )

        if query.admin_unit_id is not None:
            stmt = stmt.where(AdminUnit.id == query.admin_unit_id)

        organizations = self._batch(stmt, AdminUnit, query)
        verified = verified_admin_units(self.session, {o.id for o in organizations})
        return [
            to_organization_embed(o, verified.get(o.id, False)) for o in organizations
        ]

    def list_dump_event_categories(self) -> List[EventCategoryRefReadModel]:
        categories = (
            self.session.execute(select(EventCategory).order_by(EventCategory.id))
            .scalars()
            .all()
        )
        return [EventCategoryRefReadModel(id=c.id, name=c.name) for c in categories]

    def list_dump_event_references(
        self, query: ListDumpEventReferencesQuery
    ) -> List[DumpEventReferenceReadModel]:
        references = self._batch(select(EventReference), EventReference, query)
        return [
            DumpEventReferenceReadModel(
                id=r.id, event_id=r.event_id, admin_unit_id=r.admin_unit_id
            )
            for r in references
        ]

    def list_sitemap_events(self) -> List[SitemapEventReadModel]:
        rows = self.session.execute(
            select(Event.id, Event.created_at, Event.updated_at)
            .join(Event.admin_unit)
            .where(
                Event.dates.any(EventDate.start >= get_today()),
                Event.public_status == EventPublicStatus.published,
                AdminUnit.is_verified,
            )
            .order_by(Event.id)
        ).all()
        return [
            SitemapEventReadModel(
                id=row.id, last_modified_at=row.updated_at or row.created_at
            )
            for row in rows
        ]

    def list_organization_ids_due_for_deletion(self) -> List[ObjectId]:
        due = datetime.datetime.now(datetime.UTC) - DELETION_GRACE_PERIOD
        return self._ids(
            select(AdminUnit.id).where(AdminUnit.deletion_requested_at < due)
        )

    def list_user_ids_due_for_deletion(self) -> List[ObjectId]:
        due = datetime.datetime.now(datetime.UTC) - DELETION_GRACE_PERIOD
        return self._ids(select(User.id).where(User.deletion_requested_at < due))

    def list_ghost_user_ids(self) -> List[ObjectId]:
        created_before = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            days=31
        )
        return self._ids(
            select(User.id).where(
                User.created_at < created_before, User.confirmed_at.is_(None)
            )
        )

    def list_old_event_ids(self) -> List[ObjectId]:
        reference_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            days=366
        )
        return self._ids(
            select(Event.id).where(
                or_(Event.max_date_end.is_(None), Event.max_date_end < reference_date),
                Event.last_modified_at < reference_date,
            )
        )

    def list_recurring_event_ids(self) -> List[ObjectId]:
        return self._ids(select(Event.id).where(Event.is_recurring))

    def _ids(self, stmt) -> List[ObjectId]:
        return [
            row[0]
            for row in self.session.execute(stmt.order_by(stmt.selected_columns[0]))
        ]
