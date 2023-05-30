from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_security import current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func

from project import app, db
from project.access import (
    admin_unit_suggestions_enabled_or_404,
    can_read_event_or_401,
    get_admin_unit_members_with_permission,
)
from project.dateutils import get_next_full_hour
from project.forms.event_date import FindEventDateWidgetForm
from project.forms.event_suggestion import CreateEventSuggestionForm
from project.jsonld import get_sd_for_event_date
from project.models import AdminUnit, EventOrganizer, EventReviewStatus, EventSuggestion
from project.services.event import (
    get_event_date_with_details_or_404,
    get_event_dates_query,
)
from project.services.event_search import EventSearchParams
from project.services.event_suggestion import insert_event_suggestion
from project.services.place import get_event_places
from project.views.event import get_event_category_choices
from project.views.utils import (
    flash_errors,
    flash_message,
    get_calendar_links_for_event_date,
    get_pagination_urls,
    get_share_links,
    handleSqlError,
    send_mails,
)


@app.route("/<string:au_short_name>/widget/eventdates")
def widget_event_dates(au_short_name):
    admin_unit = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()

    params = EventSearchParams()
    params.set_default_date_range()

    form = FindEventDateWidgetForm(formdata=request.args, obj=params)
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))

    if form.validate():
        form.populate_obj(params)

    if not params.event_list_id:
        params.admin_unit_id = admin_unit.id
    dates = get_event_dates_query(params).paginate()

    return render_template(
        "widget/event_date/list.html",
        form=form,
        styles=get_styles(admin_unit),
        admin_unit=admin_unit,
        params=params,
        dates=dates.items,
        pagination=get_pagination_urls(dates, au_short_name=au_short_name),
    )


@app.route("/<string:au_short_name>/widget/eventdate/<int:id>")
def widget_event_date(au_short_name, id):
    admin_unit = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()

    event_date = get_event_date_with_details_or_404(id)
    can_read_event_or_401(event_date.event)
    structured_data = app.json.dumps(get_sd_for_event_date(event_date), indent=2)

    url = url_for("event_date", id=id, _external=True)
    share_links = get_share_links(url, event_date.event.name)
    calendar_links = get_calendar_links_for_event_date(event_date)

    return render_template(
        "widget/event_date/read.html",
        event_date=event_date,
        styles=get_styles(admin_unit),
        structured_data=structured_data,
        share_links=share_links,
        calendar_links=calendar_links,
    )


@app.route(
    "/<string:au_short_name>/widget/event_suggestions/create", methods=("GET", "POST")
)
def event_suggestion_create_for_admin_unit(au_short_name):
    admin_unit = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()
    admin_unit_suggestions_enabled_or_404(admin_unit)

    form = CreateEventSuggestionForm()

    organizers = EventOrganizer.query.filter(
        EventOrganizer.admin_unit_id == admin_unit.id
    ).order_by(func.lower(EventOrganizer.name))
    form.organizer_id.choices = [(o.id, o.name) for o in organizers]

    places = get_event_places(admin_unit.id)
    form.event_place_id.choices = [(p.id, p.name) for p in places]

    form.organizer_id.choices.insert(0, ("", ""))
    form.event_place_id.choices.insert(0, ("", ""))

    form.category_ids.choices = get_event_category_choices()

    if not form.start.data:
        form.start.data = get_next_full_hour()

    if form.validate_on_submit():
        event_suggestion = EventSuggestion()
        form.populate_obj(event_suggestion)
        event_suggestion.admin_unit_id = admin_unit.id
        event_suggestion.review_status = EventReviewStatus.inbox

        if "preview" in request.args:
            with db.session.no_autoflush:
                event_suggestion.admin_unit = admin_unit
                event_suggestion.organizer = next(
                    (o for o in organizers if o.id == event_suggestion.organizer_id),
                    None,
                )
                event_suggestion.event_place = next(
                    (p for p in places if p.id == event_suggestion.event_place_id), None
                )

            return render_template(
                "widget/event_suggestion/create_preview.html",
                admin_unit=admin_unit,
                event_suggestion=event_suggestion,
            )

        try:
            insert_event_suggestion(event_suggestion)
            db.session.commit()

            send_event_inbox_mails(admin_unit, event_suggestion)
            flash(gettext("Thank you so much! The event is being verified."), "success")

            if not current_user.is_authenticated:
                flash_message(
                    gettext(
                        "For more options and your own calendar of events, you can register for free."
                    ),
                    url_for("security.register"),
                    gettext("Register for free"),
                    "info",
                )

            return redirect(
                url_for(
                    "event_suggestion_review_status",
                    event_suggestion_id=event_suggestion.id,
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    if "preview" in request.args:
        return render_template(
            "widget/event_suggestion/create_preview.html",
            admin_unit=admin_unit,
        )

    return render_template(
        "widget/event_suggestion/create.html",
        form=form,
        admin_unit=admin_unit,
        styles=get_styles(admin_unit),
    )


def get_styles(admin_unit):
    styles = dict()

    if request.args.get("s_ft", None):
        styles["font"] = request.args["s_ft"]
    elif admin_unit.widget_font:
        styles["font"] = admin_unit.widget_font

    if request.args.get("s_bg", None):
        styles["background"] = request.args["s_bg"]
    elif admin_unit.widget_background_color:
        styles["background"] = admin_unit.widget_background_color.hex

    if request.args.get("s_pr", None):
        styles["primary"] = request.args["s_pr"]
    elif admin_unit.widget_primary_color:
        styles["primary"] = admin_unit.widget_primary_color.hex

    if request.args.get("s_li", None):
        styles["link"] = request.args["s_li"]
    elif admin_unit.widget_link_color:
        styles["link"] = admin_unit.widget_link_color.hex

    return styles


def send_event_inbox_mails(admin_unit, event_suggestion):
    members = get_admin_unit_members_with_permission(admin_unit.id, "event:verify")
    emails = list(map(lambda member: member.user.email, members))

    send_mails(
        emails,
        gettext("New event review"),
        "review_notice",
        event_suggestion=event_suggestion,
    )
