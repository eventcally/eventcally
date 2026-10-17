from dependency_injector.wiring import Provide, inject
from flask import current_app, render_template, request, url_for
from flask.wrappers import Response

from project.application.queries import (
    GetEventDateDetailQuery,
    GetEventOrganizerQuery,
    GetOrganizationQuery,
    ListUpcomingEventDatesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.forms.event_date import FindEventDateForm
from project.presentation.web.ical import create_ical_event_for_date
from project.presentation.web.jsonld import get_sd_for_event_date
from project.presentation.web.views.event import (
    get_event_category_choices,
    get_user_rights,
)
from project.presentation.web.views.event_search_params import EventSearchParams
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import (
    flash_errors,
    get_calendar_links_for_event_date,
    get_meta_data,
    get_share_links,
)
from project.shared.dateutils import create_icalendar


@inject
def prepare_event_date_form(
    form, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))
    form.location.choices = []

    organizer = None
    admin_unit = None

    if form.organizer_id.data and form.organizer_id.data > 0:
        organizer = query_bus.handle(GetEventOrganizerQuery(id=form.organizer_id.data))

        if organizer:
            form.organizer_id.choices = [(organizer.id, organizer.name)]
            admin_unit = organizer.admin_unit

    if not admin_unit and form.admin_unit_id.data and form.admin_unit_id.data > 0:
        admin_unit = query_bus.handle(GetOrganizationQuery(id=form.admin_unit_id.data))

    if admin_unit:
        form.admin_unit_id.choices = [(admin_unit.id, admin_unit.name)]

    if not form.admin_unit_id.choices:
        form.admin_unit_id.choices = []

    if not form.organizer_id.choices:
        form.organizer_id.choices = []


@main_bp.route("/eventdates")
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


@main_bp.route("/eventdate/<int:id>")
@inject
def event_date(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event_date = result_or_404(query_bus.handle(GetEventDateDetailQuery(id=id)))

    structured_data = current_app.json.dumps(
        get_sd_for_event_date(event_date), indent=2
    )

    url = url_for("main.event_date", id=id, _external=True)
    share_links = get_share_links(url, event_date.event.name)
    calendar_links = get_calendar_links_for_event_date(event_date)

    return render_template(
        "event_date/read.html",
        event_date=event_date,
        structured_data=structured_data,
        meta=get_meta_data(event_date.event, event_date),
        canonical_url=url_for("main.event_date", id=id, _external=True),
        user_rights=get_user_rights(event_date.event),
        dates=query_bus.handle(
            ListUpcomingEventDatesQuery(event_id=event_date.event.id)
        ),
        share_links=share_links,
        calendar_links=calendar_links,
    )


@main_bp.route("/eventdate/<int:id>/ical")
@inject
def event_date_ical(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    event_date = result_or_404(query_bus.handle(GetEventDateDetailQuery(id=id)))
    event = create_ical_event_for_date(event_date)

    cal = create_icalendar()
    cal.add_component(event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=eventdate_{id}.ics"},
    )
