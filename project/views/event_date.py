from project import app
from project.models import EventDate
from flask import render_template, url_for, redirect, request
from project.views.utils import flash_errors, track_analytics
import json
from project.jsonld import get_sd_for_event_date, DateTimeEncoder
from project.services.event_search import EventSearchParams
from project.forms.event_date import FindEventDateForm
from project.views.event import get_event_category_choices, get_user_rights


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
    event_date = EventDate.query.get_or_404(id)

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
        user_rights=get_user_rights(event_date.event),
    )
