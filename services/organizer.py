from models import EventOrganizer, EventPlace
from sqlalchemy import and_, or_, not_
from sqlalchemy.sql import asc, func

def upsert_event_organizer(admin_unit_id, name):
    result = EventOrganizer.query.filter(and_(EventOrganizer.name == name, EventOrganizer.admin_unit_id == admin_unit_id)).first()
    if result is None:
        result = EventOrganizer(name = name, admin_unit_id=admin_unit_id)
        result.location = Location()
        db.session.add(result)

    return result

def get_event_places(organizer_id):
    organizer = EventOrganizer.query.get(organizer_id)
    return EventPlace.query.filter(or_(EventPlace.organizer_id == organizer_id, and_(EventPlace.public, EventPlace.admin_unit_id==organizer.admin_unit_id))).order_by(func.lower(EventPlace.name)).all()