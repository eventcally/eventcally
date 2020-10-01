from app import app
from models import EventDate, Event, AdminUnit
from dateutils import today, date_set_end_of_day, form_input_from_date, form_input_to_date
from dateutil.relativedelta import relativedelta
from flask import render_template, request
from sqlalchemy import and_, or_, not_
from services.event import get_event_dates_query_for_admin_unit
from .utils import get_pagination_urls
import json
from jsonld import DateTimeEncoder, get_sd_for_event_date

@app.route("/<string:au_short_name>/widget/eventdates")
def widget_event_dates(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()

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
    dates = get_event_dates_query_for_admin_unit(admin_unit.id, date_filter, keyword).paginate()

    return render_template('widget/event_date/list.html',
        date_from_str=date_from_str,
        date_to_str=date_to_str,
        keyword=keyword,
        dates=dates.items,
        pagination=get_pagination_urls(dates, au_short_name=au_short_name))

@app.route('/widget/eventdate/<int:id>')
def widget_event_date(id):
    event_date = EventDate.query.get_or_404(id)
    structured_data = json.dumps(get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder)
    return render_template('widget/event_date/read.html',
        event_date=event_date,
        structured_data=structured_data)

@app.route("/<string:au_short_name>/widget/infoscreen")
def widget_infoscreen(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()

    #in24hours = now + relativedelta(hours=24)
    #date_filter = and_(EventDate.start >= now, EventDate.start <= in24hours)
    dates = get_event_dates_query_for_admin_unit(admin_unit.id).paginate(max_per_page=5)

    return render_template('widget/infoscreen/read.html',
        admin_unit=admin_unit,
        dates=dates.items)