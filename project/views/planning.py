from flask import render_template, request, url_for
from flask_security import auth_required

from project import app
from project.access import can_use_planning
from project.forms.planning import PlanningForm
from project.services.event_search import EventSearchParams
from project.views.event import get_event_category_choices
from project.views.utils import permission_missing


@app.route("/planning")
@auth_required()
def planning():
    if not can_use_planning():
        return permission_missing(url_for("manage_admin_units"))

    params = EventSearchParams()
    params.set_planning_date_range()

    form = PlanningForm(formdata=request.args, obj=params)
    form.category_id.choices = get_event_category_choices()
    form.category_id.data = [c[0] for c in form.category_id.choices]
    form.weekday.data = [c[0] for c in form.weekday.choices]
    form.exclude_recurring.data = True

    return render_template("planning/list.html", form=form, params=params)
