from project import app, db
from project.models import Event, EventDate, EventReviewStatus
from flask import render_template, flash, url_for, redirect, request
from flask_babelex import gettext
from project.dateutils import today, date_set_end_of_day, form_input_from_date, form_input_to_date
from dateutil.relativedelta import relativedelta
from project.views.utils import flash_errors, track_analytics, get_pagination_urls
from sqlalchemy import and_, or_, not_
import json
from project.jsonld import get_sd_for_event_date, DateTimeEncoder
from project.services.event_search import EventSearchParams
from project.services.event import get_event_dates_query
from project.forms.planing import PlaningForm
from project.views.event import get_event_category_choices

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