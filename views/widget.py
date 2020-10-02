from app import app
from models import EventDate, Event, AdminUnit
from dateutils import today, date_set_end_of_day, form_input_from_date, form_input_to_date
from dateutil.relativedelta import relativedelta
from flask import render_template, request
from sqlalchemy import and_, or_, not_
from services.event import get_event_dates_query
from services.event_search import EventSearchParams
from .utils import get_pagination_urls
import json
from jsonld import DateTimeEncoder, get_sd_for_event_date

@app.route("/<string:au_short_name>/widget/eventdates")
def widget_event_dates(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()

    params = EventSearchParams()
    params.set_default_date_range()
    params.load_from_request()
    params.admin_unit_id = admin_unit.id

    dates = get_event_dates_query(params).paginate()

    return render_template('widget/event_date/list.html',
        params=params,
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

    params = EventSearchParams()
    params.load_from_request()
    params.admin_unit_id = admin_unit.id

    dates = get_event_dates_query(params).paginate(max_per_page=5)

    return render_template('widget/infoscreen/read.html',
        admin_unit=admin_unit,
        params=params,
        dates=dates.items)