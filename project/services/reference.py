from sqlalchemy import and_
from sqlalchemy.orm import load_only

from project import db
from project.models import (
    AdminUnitRelation,
    Event,
    EventReference,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)


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


def get_reference_incoming_query(admin_unit):
    return EventReference.query.filter(EventReference.admin_unit_id == admin_unit.id)


def get_reference_outgoing_query(admin_unit):
    return EventReference.query.join(Event).filter(Event.admin_unit_id == admin_unit.id)


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
