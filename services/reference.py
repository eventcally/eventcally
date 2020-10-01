from app import db
from models import EventReference, EventReferenceRequest
from sqlalchemy import and_, or_, not_

def create_event_reference_for_request(request):
    result = EventReference.query.filter(and_(EventReference.event_id == request.event_id,
                EventReference.admin_unit_id == request.admin_unit_id)).first()

    if result is None:
        result = EventReference(event_id = request.event_id,
            admin_unit_id = request.admin_unit_id)
        db.session.add(result)

    return result
