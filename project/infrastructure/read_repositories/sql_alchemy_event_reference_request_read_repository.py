from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.orm import aliased, contains_eager, joinedload, undefer_group

from project.application.queries.list_incoming_event_reference_requests_query import (
    ListIncomingEventReferenceRequestsQuery,
)
from project.application.queries.list_outgoing_event_reference_requests_query import (
    ListOutgoingEventReferenceRequestsQuery,
)
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_reference_request_read_repository import (
    AbstractEventReferenceRequestReadRepository,
)
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId
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
from project.models import AdminUnit, AdminUnitRelation, Event, EventReferenceRequest

EventAdminUnit = aliased(AdminUnit)


def _select():
    return (
        select(EventReferenceRequest)
        .join(EventReferenceRequest.event)
        .join(EventAdminUnit, Event.admin_unit_id == EventAdminUnit.id)
        .options(
            undefer_group("trackable"),
            contains_eager(EventReferenceRequest.event)
            .load_only(Event.id, Event.name, Event.admin_unit_id)
            .contains_eager(Event.admin_unit.of_type(EventAdminUnit))
            .load_only(EventAdminUnit.id, EventAdminUnit.name),
            joinedload(EventReferenceRequest.admin_unit).load_only(
                AdminUnit.id, AdminUnit.name
            ),
        )
    )


class SqlAlchemyEventReferenceRequestReadRepository(
    AbstractEventReferenceRequestReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list_incoming(
        self, query: ListIncomingEventReferenceRequestsQuery
    ) -> Page[EventReferenceRequestReadModel]:
        return self._list(
            [EventReferenceRequest.admin_unit_id == query.admin_unit_id], query
        )

    def list_outgoing(
        self, query: ListOutgoingEventReferenceRequestsQuery
    ) -> Page[EventReferenceRequestReadModel]:
        return self._list([Event.admin_unit_id == query.admin_unit_id], query)

    def auto_verifies(
        self, source_admin_unit_id: ObjectId, target_admin_unit_id: ObjectId
    ) -> bool:
        return bool(
            self.session.execute(
                select(AdminUnitRelation.auto_verify_event_reference_requests).where(
                    AdminUnitRelation.source_admin_unit_id == source_admin_unit_id,
                    AdminUnitRelation.target_admin_unit_id == target_admin_unit_id,
                )
            ).scalar_one_or_none()
        )

    def get(self, object_id: ObjectId) -> Optional[EventReferenceRequestReadModel]:
        request = self.session.execute(
            _select()
            .where(EventReferenceRequest.id == object_id)
            .options(*audit_options(EventReferenceRequest))
        ).scalar_one_or_none()
        return (
            _to_model(request).model_copy(
                update={"audit": to_audit_read_model(request)}
            )
            if request
            else None
        )

    def _list(self, filters, query) -> Page[EventReferenceRequestReadModel]:
        if query.review_status is not None:
            filters = [
                *filters,
                EventReferenceRequest.review_status == int(query.review_status),
            ]

        filters = [*filters, *trackable_filters(EventReferenceRequest, query.trackable)]
        stmt = (
            _select()
            .where(*filters)
            .order_by(
                *trackable_order(EventReferenceRequest, query.sort),
                EventReferenceRequest.created_at.desc(),
                EventReferenceRequest.id,
            )
        )
        count_stmt = (
            select(EventReferenceRequest.id)
            .join(EventReferenceRequest.event)
            .where(*filters)
        )
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )


def _to_model(request) -> EventReferenceRequestReadModel:
    return EventReferenceRequestReadModel(
        id=request.id,
        admin_unit_id=request.admin_unit_id,
        event_id=request.event_id,
        review_status=EventReferenceRequestReviewStatus(request.review_status),
        rejection_reason=(
            EventReferenceRequestRejectionReason(request.rejection_reason)
            if request.rejection_reason
            else None
        ),
        created_at=request.created_at,
        updated_at=request.updated_at,
        event=to_event_ref_read_model(request.event),
        admin_unit=to_organization_ref_read_model(request.admin_unit),
    )
