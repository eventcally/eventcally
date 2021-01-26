from project import app, db
from project.models import (
    User,
    AdminUnit,
    EventOrganizer,
    EventSuggestion,
    EventReviewStatus,
    AdminUnitMember,
)
from flask import render_template, request, flash, redirect, url_for, abort
from flask_babelex import gettext
from flask_security import current_user
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from project.services.event_suggestion import insert_event_suggestion
from project.services.event import (
    get_event_dates_query,
    get_event_date_with_details_or_404,
)
from project.services.event_search import EventSearchParams
from project.services.place import get_event_places
from project.views.utils import (
    get_pagination_urls,
    flash_errors,
    flash_message,
    send_mail,
    handleSqlError,
)
import json
from project.jsonld import DateTimeEncoder, get_sd_for_event_date
from project.forms.event_date import FindEventDateForm
from project.forms.event_suggestion import CreateEventSuggestionForm
from project.views.event_date import prepare_event_date_form
from project.views.event import get_event_category_choices
from project.access import has_admin_unit_member_permission


@app.route("/<string:au_short_name>/widget/eventdates")
def widget_event_dates(au_short_name):
    admin_unit = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()

    params = EventSearchParams()
    params.set_default_date_range()

    form = FindEventDateForm(formdata=request.args, obj=params)
    prepare_event_date_form(form)

    if form.validate():
        form.populate_obj(params)

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
    structured_data = json.dumps(
        get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder
    )
    return render_template(
        "widget/event_date/read.html",
        event_date=event_date,
        styles=get_styles(admin_unit),
        structured_data=structured_data,
    )


@app.route("/<string:au_short_name>/widget/infoscreen")
def widget_infoscreen(au_short_name):
    admin_unit = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()

    params = EventSearchParams()
    params.load_from_request()
    params.admin_unit_id = admin_unit.id

    dates = get_event_dates_query(params).paginate(max_per_page=5)

    return render_template(
        "widget/infoscreen/read.html",
        admin_unit=admin_unit,
        params=params,
        styles=get_styles(admin_unit),
        dates=dates.items,
    )


@app.route(
    "/<string:au_short_name>/widget/event_suggestions/create", methods=("GET", "POST")
)
def event_suggestion_create_for_admin_unit(au_short_name):
    admin_unit = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()

    form = CreateEventSuggestionForm()
    form.organizer_id.choices = [
        (o.id, o.name)
        for o in EventOrganizer.query.filter(
            EventOrganizer.admin_unit_id == admin_unit.id
        ).order_by(func.lower(EventOrganizer.name))
    ]

    places = get_event_places(admin_unit.id)
    form.event_place_id.choices = [(p.id, p.name) for p in places]

    form.organizer_id.choices.insert(0, ("", ""))
    form.event_place_id.choices.insert(0, ("", ""))

    form.category_ids.choices = get_event_category_choices()

    if form.validate_on_submit():
        event_suggestion = EventSuggestion()
        form.populate_obj(event_suggestion)
        event_suggestion.admin_unit_id = admin_unit.id
        event_suggestion.review_status = EventReviewStatus.inbox

        if "preview" in request.args:
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
        if "preview" in request.args:
            abort(406)
        flash_errors(form)

    return render_template(
        "widget/event_suggestion/create.html",
        form=form,
        admin_unit=admin_unit,
        styles=get_styles(admin_unit),
    )


def get_styles(admin_unit):
    styles = dict()

    if admin_unit.widget_font:
        styles["font"] = admin_unit.widget_font

    if admin_unit.widget_background_color:
        styles["background"] = admin_unit.widget_background_color.hex

    if admin_unit.widget_primary_color:
        styles["primary"] = admin_unit.widget_primary_color.hex

    if admin_unit.widget_link_color:
        styles["link"] = admin_unit.widget_link_color.hex

    return styles


def send_event_inbox_mails(admin_unit, event_suggestion):
    members = (
        AdminUnitMember.query.join(User)
        .filter(AdminUnitMember.admin_unit_id == admin_unit.id)
        .all()
    )

    for member in members:
        if has_admin_unit_member_permission(member, "event:verify"):
            send_mail(
                member.user.email,
                gettext("New event review"),
                "review_notice",
                event_suggestion=event_suggestion,
            )
