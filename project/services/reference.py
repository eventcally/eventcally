from sqlalchemy import and_
from sqlalchemy.orm import defaultload, joinedload, load_only

from project import db
from project.models import (
    AdminUnitRelation,
    Event,
    EventReference,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from project.models.admin_unit import AdminUnit
from project.services.search_params import EventReferenceSearchParams


def create_event_reference_for_request(request):
    return upsert_event_reference(request.event_id, request.admin_unit_id)


def get_event_reference(event_id: int, admin_unit_id: int):
    return EventReference.query.filter(
        and_(
            EventReference.event_id == event_id,
            EventReference.admin_unit_id == admin_unit_id,
        )
    ).first()


def upsert_event_reference(event_id: int, admin_unit_id: int):
    result = get_event_reference(event_id, admin_unit_id)

    if result is None:
        result = EventReference(event_id=event_id, admin_unit_id=admin_unit_id)
        result.rating = 50
        db.session.add(result)

    return result


def get_reference_incoming_query(params: EventReferenceSearchParams):
    result = EventReference.query

    if params.admin_unit_id:
        result = result.filter(EventReference.admin_unit_id == params.admin_unit_id)

    result = params.get_trackable_query(result, EventReference)
    result = params.get_trackable_order_by(result, EventReference)
    result = result.order_by(EventReference.created_at.desc())
    return result


def get_reference_outgoing_query(admin_unit):
    return (
        EventReference.query.join(Event)
        .filter(Event.admin_unit_id == admin_unit.id)
        .order_by(EventReference.created_at.desc())
    )


def get_reference_requests_incoming_query(admin_unit):
    return EventReferenceRequest.query.filter(
        and_(
            EventReferenceRequest.review_status
            != EventReferenceRequestReviewStatus.verified,
            EventReferenceRequest.admin_unit_id == admin_unit.id,
        )
    )


def get_reference_requests_incoming_badge_query(admin_unit):
    return EventReferenceRequest.query.options(
        load_only(EventReferenceRequest.id)
    ).filter(
        and_(
            EventReferenceRequest.review_status
            == EventReferenceRequestReviewStatus.inbox,
            EventReferenceRequest.admin_unit_id == admin_unit.id,
        )
    )


def get_relation_outgoing_query(admin_unit):
    return AdminUnitRelation.query.filter(
        AdminUnitRelation.source_admin_unit_id == admin_unit.id
    )


def get_newest_reference_requests(admin_unit_id: int, limit: int):
    return (
        EventReferenceRequest.query.join(
            Event, EventReferenceRequest.event_id == Event.id
        )
        .join(
            AdminUnit,
            EventReferenceRequest.admin_unit_id == AdminUnit.id,
        )
        .options(
            load_only(EventReferenceRequest.id),
            defaultload(EventReferenceRequest.event).load_only(Event.id),
            joinedload(EventReferenceRequest.admin_unit).load_only(
                AdminUnit.id, AdminUnit.name
            ),
        )
        .filter(
            and_(
                Event.admin_unit_id == admin_unit_id,
                AdminUnit.id != admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
        )
        .order_by(EventReferenceRequest.created_at.desc())
        .limit(limit)
        .all()
    )


def get_newest_references(admin_unit_id: int, limit: int):
    return (
        EventReference.query.join(Event, EventReference.event_id == Event.id)
        .join(
            AdminUnit,
            EventReference.admin_unit_id == AdminUnit.id,
        )
        .options(
            load_only(EventReference.id),
            defaultload(EventReference.event).load_only(Event.id),
            joinedload(EventReference.admin_unit).load_only(
                AdminUnit.id, AdminUnit.name
            ),
        )
        .filter(
            and_(
                Event.admin_unit_id == admin_unit_id,
                AdminUnit.id != admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
        )
        .order_by(EventReference.created_at.desc())
        .limit(limit)
        .all()
    )
