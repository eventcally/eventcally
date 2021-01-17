from project import db
from project.models import (
    Event,
    EventReference,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from sqlalchemy import and_


def create_event_reference_for_request(request):
    result = EventReference.query.filter(
        and_(
            EventReference.event_id == request.event_id,
            EventReference.admin_unit_id == request.admin_unit_id,
        )
    ).first()

    if result is None:
        result = EventReference(
            event_id=request.event_id, admin_unit_id=request.admin_unit_id
        )
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
    return EventReferenceRequest.query.filter(
        and_(
            EventReferenceRequest.review_status
            == EventReferenceRequestReviewStatus.inbox,
            EventReferenceRequest.admin_unit_id == admin_unit.id,
        )
    )
