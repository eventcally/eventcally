from app import app, db
from models import Event, EventDate, EventReviewStatus
from flask import render_template, flash, url_for, redirect, request
from flask_babelex import gettext
from dateutils import today, date_set_end_of_day, form_input_from_date, form_input_to_date
from dateutil.relativedelta import relativedelta
from .utils import flash_errors, track_analytics, get_pagination_urls
from sqlalchemy import and_, or_, not_
import json
from jsonld import get_sd_for_event_date, DateTimeEncoder

@app.route("/eventdates")
def event_dates():
    date_from = today
    date_to = date_set_end_of_day(today + relativedelta(months=12))
    date_from_str = form_input_from_date(date_from)
    date_to_str = form_input_from_date(date_to)
    keyword = ''

    if 'date_from' in request.args:
        date_from_str = request.args['date_from']
        date_from = form_input_to_date(date_from_str)

    if 'date_to' in request.args:
        date_to_str = request.args['date_to']
        date_to = form_input_to_date(date_to_str)

    if 'keyword' in request.args:
        keyword = request.args['keyword']

    date_filter = and_(EventDate.start >= date_from, EventDate.start < date_to)

    if keyword:
        like_keyword = '%' + keyword + '%'
        event_filter = and_(Event.verified, or_(Event.name.ilike(like_keyword), Event.description.ilike(like_keyword), Event.tags.ilike(like_keyword)))
    else:
        event_filter = Event.verified

    dates = EventDate.query.join(Event).filter(date_filter).filter(event_filter).order_by(EventDate.start).paginate()

    return render_template('event_date/list.html',
        date_from_str=date_from_str,
        date_to_str=date_to_str,
        keyword=keyword,
        dates=dates.items,
        pagination=get_pagination_urls(dates))

@app.route('/eventdate/<int:id>')
def event_date(id):
    event_date = EventDate.query.get_or_404(id)

    if 'src' in request.args:
        track_analytics("event_date", str(id), request.args['src'])
        return redirect(url_for('event_date', id=id))

    structured_data = json.dumps(get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder)
    return render_template('event_date/read.html',
        event_date=event_date,
        structured_data=structured_data)