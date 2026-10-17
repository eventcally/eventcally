from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.orm import aliased, contains_eager, joinedload, undefer_group

from project.application.queries.list_incoming_event_references_query import (
    ListIncomingEventReferencesQuery,
)
from project.application.queries.list_outgoing_event_references_query import (
    ListOutgoingEventReferencesQuery,
)
from project.application.read_models.event_reference_read_models import (
    EventReferenceReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_reference_read_repository import (
    AbstractEventReferenceReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, Event, EventReference
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
    trackable_order,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
    to_event_ref_read_model,
    to_organization_ref_read_model,
)

EventAdminUnit = aliased(AdminUnit)


def _select():
    return (
        select(EventReference)
        .join(EventReference.event)
        .join(EventAdminUnit, Event.admin_unit_id == EventAdminUnit.id)
        .options(
            undefer_group("trackable"),
            contains_eager(EventReference.event)
            .load_only(Event.id, Event.name, Event.admin_unit_id)
            .contains_eager(Event.admin_unit.of_type(EventAdminUnit))
            .load_only(EventAdminUnit.id, EventAdminUnit.name),
            joinedload(EventReference.admin_unit).load_only(
                AdminUnit.id, AdminUnit.name
            ),
        )
    )


class SqlAlchemyEventReferenceReadRepository(AbstractEventReferenceReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list_incoming(
        self, query: ListIncomingEventReferencesQuery
    ) -> Page[EventReferenceReadModel]:
        return self._list([EventReference.admin_unit_id == query.admin_unit_id], query)

    def list_outgoing(
        self, query: ListOutgoingEventReferencesQuery
    ) -> Page[EventReferenceReadModel]:
        return self._list([Event.admin_unit_id == query.admin_unit_id], query)

    def get(self, object_id: ObjectId) -> Optional[EventReferenceReadModel]:
        reference = (
            self.session.execute(
                _select()
                .where(EventReference.id == object_id)
                .options(*audit_options(EventReference))
            )
            .unique()
            .scalar_one_or_none()
        )
        return (
            _to_model(reference).model_copy(
                update={"audit": to_audit_read_model(reference)}
            )
            if reference
            else None
        )

    def _list(self, filters, query) -> Page[EventReferenceReadModel]:
        filters = [*filters, *trackable_filters(EventReference, query.trackable)]
        stmt = (
            _select()
            .where(*filters)
            .order_by(
                *trackable_order(EventReference, query.sort),
                EventReference.created_at.desc(),
                EventReference.id,
            )
        )
        count_stmt = (
            select(EventReference.id).join(EventReference.event).where(*filters)
        )
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )


def _to_model(reference) -> EventReferenceReadModel:
    return EventReferenceReadModel(
        id=reference.id,
        admin_unit_id=reference.admin_unit_id,
        event_id=reference.event_id,
        rating=reference.rating,
        created_at=reference.created_at,
        updated_at=reference.updated_at,
        event=to_event_ref_read_model(reference.event),
        admin_unit=to_organization_ref_read_model(reference.admin_unit),
    )
