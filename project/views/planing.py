from project import app
from flask import render_template, request
from project.services.event_search import EventSearchParams
from project.forms.planing import PlaningForm
from project.views.event import get_event_category_choices


def prepare_event_date_form(form):
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))


@app.route("/planing")
def planing():
    params = EventSearchParams()
    params.set_planing_date_range()

    form = PlaningForm(formdata=request.args, obj=params)
    prepare_event_date_form(form)

    return render_template("planing/list.html", form=form, params=params)
