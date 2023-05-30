from sqlalchemy.sql import and_, func

from project import db
from project.models import EventPlace, Location


def get_event_place(admin_unit_id, name):
    return EventPlace.query.filter(
        and_(
            EventPlace.name == name,
            EventPlace.admin_unit_id == admin_unit_id,
        )
    ).first()


def upsert_event_place(admin_unit_id, name):
    result = get_event_place(admin_unit_id, name)
    if result is None:
        result = EventPlace(name=name, admin_unit_id=admin_unit_id)
        result.location = Location()
        db.session.add(result)

    return result


def get_event_places(admin_unit_id, keyword=None, limit=None):
    query = EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)

    if keyword:
        like_keyword = "%" + keyword + "%"
        order_keyword = keyword + "%"
        query = query.filter(EventPlace.name.ilike(like_keyword))
        query = query.order_by(
            EventPlace.name.ilike(order_keyword).desc(), func.lower(EventPlace.name)
        )
    else:
        query = query.order_by(func.lower(EventPlace.name))

    if limit:
        query = query.limit(5)

    return query.all()
