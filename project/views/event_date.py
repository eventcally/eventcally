import json

from flask import redirect, render_template, request, url_for
from flask.wrappers import Response

from project import app
from project.access import can_read_event_or_401
from project.dateutils import create_icalendar
from project.forms.event_date import FindEventDateForm
from project.jsonld import DateTimeEncoder, get_sd_for_event_date
from project.services.event import (
    create_ical_event_for_date,
    get_event_date_with_details_or_404,
    get_meta_data,
    get_upcoming_event_dates,
)
from project.services.event_search import EventSearchParams
from project.views.event import get_event_category_choices, get_menu_user_rights
from project.views.utils import (
    flash_errors,
    get_calendar_links,
    get_share_links,
    track_analytics,
)


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


@app.route("/eventdatesearch")
def event_date_search():
    return render_template("event_date/search.html")


@app.route("/eventdate/<int:id>")
def event_date(id):
    event_date = get_event_date_with_details_or_404(id)
    can_read_event_or_401(event_date.event)

    if "src" in request.args:
        track_analytics("event_date", str(id), request.args["src"])
        return redirect(url_for("event_date", id=id))

    structured_data = json.dumps(
        get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder
    )

    url = url_for("event_date", id=id, _external=True)
    share_links = get_share_links(url, event_date.event.name)
    calendar_links = get_calendar_links(event_date)

    return render_template(
        "event_date/read.html",
        event_date=event_date,
        structured_data=structured_data,
        meta=get_meta_data(event_date.event, event_date),
        canonical_url=url_for("event_date", id=id, _external=True),
        user_rights=get_menu_user_rights(event_date.event),
        dates=get_upcoming_event_dates(event_date.event_id),
        share_links=share_links,
        calendar_links=calendar_links,
    )


@app.route("/eventdate/<int:id>/ical")
def event_date_ical(id):
    event_date = get_event_date_with_details_or_404(id)
    can_read_event_or_401(event_date.event)
    event = create_ical_event_for_date(event_date)

    cal = create_icalendar()
    cal.add_component(event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=eventdate_{id}.ics"},
    )
