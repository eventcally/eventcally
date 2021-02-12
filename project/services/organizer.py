from sqlalchemy import and_

from project import db
from project.models import EventOrganizer, Location


def get_event_organizer(admin_unit_id, name):
    return EventOrganizer.query.filter(
        and_(EventOrganizer.name == name, EventOrganizer.admin_unit_id == admin_unit_id)
    ).first()


def upsert_event_organizer(admin_unit_id, name):
    result = get_event_organizer(admin_unit_id, name)
    if result is None:
        result = EventOrganizer(name=name, admin_unit_id=admin_unit_id)
        result.location = Location()
        db.session.add(result)

    return result
