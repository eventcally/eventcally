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
from services.event_search import EventSearchParams
from services.event import get_event_dates_query

@app.route("/eventdates")
def event_dates():
    params = EventSearchParams()
    params.set_default_date_range()
    params.load_from_request()

    dates = get_event_dates_query(params).paginate()

    return render_template('event_date/list.html',
        params=params,
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