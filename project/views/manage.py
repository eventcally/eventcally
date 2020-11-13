from project import app, db
from project.models import (
    AdminUnitMember,
    AdminUnitMemberInvitation,
    EventPlace,
    EventOrganizer,
    User,
    EventSuggestion,
)
from flask import (
    render_template,
    flash,
    url_for,
    redirect,
    request,
    make_response,
)
from flask_babelex import gettext
from flask_security import auth_required, current_user
from project.access import (
    has_access,
    get_admin_unit_for_manage,
    get_admin_units_for_manage,
    get_admin_unit_for_manage_or_404,
)
from sqlalchemy.sql import desc, func
from sqlalchemy.exc import SQLAlchemyError
from project.views.utils import (
    get_pagination_urls,
    permission_missing,
    handleSqlError,
    flash_errors,
)
from project.forms.event_place import FindEventPlaceForm
from project.forms.event import FindEventForm
from project.forms.admin_unit import UpdateAdminUnitWidgetForm
from project.services.event_search import EventSearchParams
from project.services.event import get_events_query
from project.services.event_suggestion import get_event_reviews_query
from project.views.event import get_event_category_choices


@app.route("/manage")
@auth_required()
def manage():
    try:
        if "manage_admin_unit_id" in request.cookies:
            manage_admin_unit_id = int(request.cookies.get("manage_admin_unit_id"))
            admin_unit = get_admin_unit_for_manage(manage_admin_unit_id)

            if admin_unit:
                return redirect(url_for("manage_admin_unit", id=admin_unit.id))
    except Exception:
        pass

    return redirect(url_for("manage_admin_units"))


@app.route("/manage/admin_units")
@auth_required()
def manage_admin_units():
    admin_units = get_admin_units_for_manage()
    invitations = AdminUnitMemberInvitation.query.filter(
        AdminUnitMemberInvitation.email == current_user.email
    ).all()

    admin_units.sort(key=lambda x: x.name)
    invitations.sort(key=lambda x: x.adminunit.name)

    return render_template(
        "manage/admin_units.html", invitations=invitations, admin_units=admin_units
    )


@app.route("/manage/admin_unit/<int:id>")
@auth_required()
def manage_admin_unit(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    response = make_response(
        redirect(url_for("manage_admin_unit_events", id=admin_unit.id))
    )
    response.set_cookie("manage_admin_unit_id", str(admin_unit.id))
    return response


@app.route("/manage/admin_unit/<int:id>/reviews")
@auth_required()
def manage_admin_unit_event_reviews(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    event_suggestions_paginate = (
        get_event_reviews_query(admin_unit)
        .order_by(desc(EventSuggestion.created_at))
        .paginate()
    )
    event_suggestions = event_suggestions_paginate.items

    return render_template(
        "manage/reviews.html",
        admin_unit=admin_unit,
        event_suggestions=event_suggestions,
        pagination=get_pagination_urls(event_suggestions_paginate, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/events")
@auth_required()
def manage_admin_unit_events(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    params = EventSearchParams()
    params.set_default_date_range()

    form = FindEventForm(formdata=request.args, obj=params)
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))

    organizers = (
        EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id)
        .order_by(func.lower(EventOrganizer.name))
        .all()
    )
    form.organizer_id.choices = [(o.id, o.name) for o in organizers]
    form.organizer_id.choices.insert(0, (0, ""))

    if form.validate():
        form.populate_obj(params)

    params.admin_unit_id = admin_unit.id
    events = get_events_query(params).paginate()
    return render_template(
        "manage/events.html",
        admin_unit=admin_unit,
        form=form,
        events=events.items,
        pagination=get_pagination_urls(events, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/organizers")
@auth_required()
def manage_admin_unit_organizers(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizers = (
        EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id)
        .order_by(func.lower(EventOrganizer.name))
        .paginate()
    )

    return render_template(
        "manage/organizers.html",
        admin_unit=admin_unit,
        organizers=organizers.items,
        pagination=get_pagination_urls(organizers, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/event_places")
@auth_required()
def manage_admin_unit_event_places(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    form = FindEventPlaceForm(**request.args)

    places = (
        EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit.id)
        .order_by(func.lower(EventPlace.name))
        .paginate()
    )
    return render_template(
        "manage/places.html",
        admin_unit=admin_unit,
        form=form,
        places=places.items,
        pagination=get_pagination_urls(places, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/members")
@auth_required()
def manage_admin_unit_members(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "admin_unit.members:read"):
        return permission_missing(url_for("manage_admin_unit", id=id))

    members = (
        AdminUnitMember.query.join(User)
        .filter(AdminUnitMember.admin_unit_id == admin_unit.id)
        .order_by(func.lower(User.email))
        .paginate()
    )
    invitations = (
        AdminUnitMemberInvitation.query.filter(
            AdminUnitMemberInvitation.admin_unit_id == admin_unit.id
        )
        .order_by(func.lower(AdminUnitMemberInvitation.email))
        .all()
    )

    return render_template(
        "manage/members.html",
        admin_unit=admin_unit,
        can_invite_users=has_access(admin_unit, "admin_unit.members:invite"),
        members=members.items,
        invitations=invitations,
        pagination=get_pagination_urls(members, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/widgets", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_widgets(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    default_background_color = "#ffffff"
    default_primary_color = "#007bff"

    form = UpdateAdminUnitWidgetForm(obj=admin_unit)

    if not form.widget_background_color.data:
        form.widget_background_color.data = default_background_color

    if not form.widget_primary_color.data:
        form.widget_primary_color.data = default_primary_color

    if not form.widget_link_color.data:
        form.widget_link_color.data = default_primary_color

    if form.validate_on_submit():
        if not has_access(admin_unit, "admin_unit:update"):
            return permission_missing(url_for("manage_admin_unit", id=admin_unit.id))

        form.populate_obj(admin_unit)

        if form.widget_background_color.data == default_background_color:
            admin_unit.widget_background_color = None

        if form.widget_primary_color.data == default_primary_color:
            admin_unit.widget_primary_color = None

        if form.widget_link_color.data == default_primary_color:
            admin_unit.widget_link_color = None

        try:
            db.session.commit()
            flash(gettext("Settings successfully updated"), "success")
            return redirect(url_for("manage_admin_unit_widgets", id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("manage/widgets.html", form=form, admin_unit=admin_unit)
