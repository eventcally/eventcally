import json

from flask import redirect, render_template, request, url_for

from project import app
from project.forms.event_date import FindEventDateForm
from project.jsonld import DateTimeEncoder, get_sd_for_event_date
from project.services.event import (
    get_event_date_with_details_or_404,
    get_upcoming_event_dates,
)
from project.services.event_search import EventSearchParams
from project.views.event import get_event_category_choices, get_menu_user_rights
from project.views.utils import flash_errors, track_analytics, truncate


def prepare_event_date_form(form):
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))


@app.route("/eventdates")
def event_dates():
    params = EventSearchParams()
    params.set_default_date_range()

    form = FindEventDateForm(formdata=request.args, obj=params)
    prepare_event_date_form(form)

    if form.validate():
        form.populate_obj(params)
    else:
        flash_errors(form)

    return render_template("event_date/list.html", form=form, params=params)


@app.route("/eventdate/<int:id>")
def event_date(id):
    event_date = get_event_date_with_details_or_404(id)

    if "src" in request.args:
        track_analytics("event_date", str(id), request.args["src"])
        return redirect(url_for("event_date", id=id))

    structured_data = json.dumps(
        get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder
    )
    return render_template(
        "event_date/read.html",
        event_date=event_date,
        structured_data=structured_data,
        meta_description=truncate(event_date.event.description, 300),
        canonical_url=url_for("event_date", id=id, _external=True),
        user_rights=get_menu_user_rights(event_date.event),
        dates=get_upcoming_event_dates(event_date.event_id),
    )
