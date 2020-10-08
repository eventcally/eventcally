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
from forms.planing import PlaningForm
from .event import get_event_category_choices

def prepare_event_date_form(form):
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ''))

@app.route("/planing")
def planing():
    params = EventSearchParams()
    params.set_planing_date_range()

    form = PlaningForm(formdata=request.args, obj=params)
    prepare_event_date_form(form)

    return render_template('planing/list.html',
        form=form,
        params=params)