from flask import render_template, request, url_for
from flask.wrappers import Response

from project import app, db
from project.access import can_read_event_or_401
from project.dateutils import create_icalendar
from project.forms.event_date import FindEventDateForm
from project.jsonld import get_sd_for_event_date
from project.models import AdminUnit, EventOrganizer
from project.services.event import (
    create_ical_event_for_date,
    get_event_date_with_details_or_404,
    get_meta_data,
    get_upcoming_event_dates,
)
from project.services.search_params import EventSearchParams
from project.views.event import get_event_category_choices, get_user_rights
from project.views.utils import (
    flash_errors,
    get_calendar_links_for_event_date,
    get_share_links,
)


def prepare_event_date_form(form):
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))
    form.location.choices = []

    organizer = None
    admin_unit = None

    if form.organizer_id.data and form.organizer_id.data > 0:
        organizer = db.session.get(EventOrganizer, form.organizer_id.data)

        if organizer:
            form.organizer_id.choices = [(organizer.id, organizer.name)]
            admin_unit = organizer.admin_unit

    if not admin_unit and form.admin_unit_id.data and form.admin_unit_id.data > 0:
        admin_unit = db.session.get(AdminUnit, form.admin_unit_id.data)

    if admin_unit:
        form.admin_unit_id.choices = [(admin_unit.id, admin_unit.name)]

    if not form.admin_unit_id.choices:
        form.admin_unit_id.choices = []

    if not form.organizer_id.choices:
        form.organizer_id.choices = []


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
    can_read_event_or_401(event_date.event)

    structured_data = app.json.dumps(get_sd_for_event_date(event_date), indent=2)

    url = url_for("event_date", id=id, _external=True)
    share_links = get_share_links(url, event_date.event.name)
    calendar_links = get_calendar_links_for_event_date(event_date)

    return render_template(
        "event_date/read.html",
        event_date=event_date,
        structured_data=structured_data,
        meta=get_meta_data(event_date.event, event_date),
        canonical_url=url_for("event_date", id=id, _external=True),
        user_rights=get_user_rights(event_date.event),
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
