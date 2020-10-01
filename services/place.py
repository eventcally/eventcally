from models import EventPlace

def upsert_event_place(admin_unit_id, organizer_id, name):
    result = EventPlace.query.filter(and_(EventPlace.name == name, EventPlace.admin_unit_id == admin_unit_id, EventPlace.organizer_id == organizer_id)).first()
    if result is None:
        result = EventPlace(name = name, admin_unit_id=admin_unit_id, organizer_id=organizer_id)
        result.location = Location()
        db.session.add(result)

    return result