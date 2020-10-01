from models import EventCategory, Event, EventDate, EventReference
from dateutils import dates_from_recurrence_rule, today, date_add_time
from sqlalchemy import and_, or_, not_

def upsert_event_category(category_name):
    result = EventCategory.query.filter_by(name = category_name).first()
    if result is None:
        result = EventCategory(name = category_name)
        db.session.add(result)

    return result

def get_event_dates_query_for_admin_unit(admin_unit_id, date_filter = None, keyword = None):
    my_event_filter = and_(or_(Event.admin_unit_id == admin_unit_id, Event.references.any(EventReference.admin_unit_id == admin_unit_id)), Event.verified)
    my_date_filter = date_filter if date_filter is not None else (EventDate.start >= today)

    if keyword:
        like_keyword = '%' + keyword + '%'
        my_event_filter = and_(my_event_filter, or_(Event.name.ilike(like_keyword), Event.description.ilike(like_keyword), Event.tags.ilike(like_keyword)))

    return EventDate.query.join(Event).filter(my_date_filter).filter(my_event_filter).order_by(EventDate.start)

def update_event_dates_with_recurrence_rule(event, start, end):
    event.start = start
    event.end = end

    if end:
        time_difference = relativedelta(end, start)

    dates_to_add = list()
    dates_to_remove = list(event.dates)

    if event.recurrence_rule:
        rr_dates = dates_from_recurrence_rule(start, event.recurrence_rule)
    else:
        rr_dates = [start]

    for rr_date in rr_dates:
        rr_date_start = date_add_time(rr_date, start.hour, start.minute, start.second, rr_date.tzinfo)

        if end:
            rr_date_end = rr_date_start + time_difference
        else:
            rr_date_end = None

        existing_date = next((date for date in event.dates if date.start == rr_date_start and date.end == rr_date_end), None)
        if existing_date:
            dates_to_remove.remove(existing_date)
        else:
            new_date = EventDate(event_id = event.id, start=rr_date_start, end=rr_date_end)
            dates_to_add.append(new_date)

    event.dates = [date for date in event.dates if date not in dates_to_remove]
    event.dates.extend(dates_to_add)