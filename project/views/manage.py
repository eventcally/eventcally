import os

from flask import (
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_babel import gettext
from flask_security import auth_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import desc, func

from project import app, db, dump_org_path
from project.access import (
    access_or_401,
    admin_unit_suggestions_enabled_or_404,
    can_current_user_delete_member,
    get_admin_unit_for_manage_or_404,
    get_admin_units_for_manage,
    has_access,
)
from project.celery_tasks import dump_admin_unit_task
from project.forms.admin_unit import (
    AdminUnitDeleteMembershipForm,
    UpdateAdminUnitWidgetForm,
)
from project.forms.event import FindEventForm
from project.models import (
    AdminUnitMember,
    AdminUnitMemberInvitation,
    EventOrganizer,
    EventPlace,
    EventSuggestion,
    User,
)
from project.services.admin_unit import (
    get_admin_unit_member_invitations,
    get_admin_unit_organization_invitations,
    get_member_for_admin_unit_by_user_id,
)
from project.services.event import get_events_query
from project.services.event_suggestion import get_event_reviews_query
from project.services.search_params import EventSearchParams
from project.utils import get_place_str
from project.views.event import get_event_category_choices
from project.views.utils import (
    flash_errors,
    get_celery_poll_result,
    get_current_admin_unit,
    get_pagination_urls,
    handleSqlError,
    non_match_for_deletion,
    permission_missing,
    set_current_admin_unit,
)


@app.route("/manage_after_login")
@auth_required()
def manage_after_login():
    return redirect(url_for("manage", from_login=1))


@app.route("/manage")
@auth_required()
def manage():
    admin_unit = get_current_admin_unit(False)

    if admin_unit:
        return redirect(url_for("manage_admin_unit", id=admin_unit.id))

    if "from_login" in request.args:
        admin_units = get_admin_units_for_manage()
        invitations = get_admin_unit_member_invitations(current_user.email)
        organization_invitations = get_admin_unit_organization_invitations(
            current_user.email
        )

        if (
            len(admin_units) == 1
            and len(invitations) == 0
            and len(organization_invitations) == 0
        ):
            return redirect(url_for("manage_admin_unit", id=admin_units[0].id))

        if (
            len(admin_units) == 0
            and len(invitations) == 1
            and len(organization_invitations) == 0
        ):
            return redirect(
                url_for("admin_unit_member_invitation", id=invitations[0].id)
            )

        if (
            len(admin_units) == 0
            and len(invitations) == 0
            and len(organization_invitations) == 1
        ):
            return redirect(
                url_for(
                    "user_organization_invitation", id=organization_invitations[0].id
                )
            )

    return redirect(url_for("manage_admin_units"))


@app.route("/manage/admin_units")
@auth_required()
def manage_admin_units():
    admin_units = get_admin_units_for_manage()
    invitations = get_admin_unit_member_invitations(current_user.email)
    organization_invitations = get_admin_unit_organization_invitations(
        current_user.email
    )

    admin_units.sort(key=lambda x: x.name)
    invitations.sort(key=lambda x: x.adminunit.name)
    organization_invitations.sort(key=lambda x: x.adminunit.name)

    return render_template(
        "manage/admin_units.html",
        invitations=invitations,
        organization_invitations=organization_invitations,
        admin_units=admin_units,
    )


@app.route("/manage/admin_unit/<int:id>")
@auth_required()
def manage_admin_unit(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)
    return redirect(url_for("manage_admin_unit_events", id=admin_unit.id))


@app.route("/manage/admin_unit/<int:id>/reviews")
@auth_required()
def manage_admin_unit_event_reviews(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)
    admin_unit_suggestions_enabled_or_404(admin_unit)

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
    set_current_admin_unit(admin_unit)

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

    event_places = (
        EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit.id)
        .order_by(func.lower(EventPlace.name))
        .all()
    )
    form.event_place_id.choices = [(p.id, get_place_str(p)) for p in event_places]
    form.event_place_id.choices.insert(0, (0, ""))

    if form.location.data:  # pragma: no cover
        form.location.choices = [(form.location.data, form.location_name.data)]
    else:
        form.location.choices = []

    if form.validate():
        form.populate_obj(params)

    params.admin_unit_id = admin_unit.id
    params.can_read_private_events = True
    events = get_events_query(params).paginate(per_page=50)
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
    set_current_admin_unit(admin_unit)

    organizers = (
        EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id)
        .order_by(func.lower(EventOrganizer.name))
        .paginate(per_page=50)
    )

    return render_template(
        "manage/organizers.html",
        admin_unit=admin_unit,
        organizers=organizers.items,
        pagination=get_pagination_urls(organizers, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/members")
@auth_required()
def manage_admin_unit_members(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

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


@app.route("/manage/admin_unit/<int:id>/membership/delete", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_delete_membership(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

    member = get_member_for_admin_unit_by_user_id(
        admin_unit.id,
        current_user.id,
    )

    if not member:
        # E.g. global admin
        flash(gettext("You are not a member of this organization"), "danger")
        return redirect(url_for("manage_admin_unit_members", id=id))

    if not can_current_user_delete_member(member):
        flash(
            gettext("Last remaining administrator can not leave the organization."),
            "danger",
        )
        return redirect(url_for("manage_admin_unit_members", id=id))

    form = AdminUnitDeleteMembershipForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.name.data, admin_unit.name):
            flash(gettext("Entered name does not match organization name"), "danger")
        else:
            try:
                db.session.delete(member)
                db.session.commit()
                flash(gettext("Organization successfully left"), "success")
                return redirect(url_for("manage_admin_units"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "manage/delete_membership.html",
        admin_unit=admin_unit,
        member=member,
        form=form,
    )


@app.route("/manage/admin_unit/<int:id>/relations")
@app.route("/manage/admin_unit/<int:id>/relations/<path:path>")
@auth_required()
def manage_admin_unit_relations(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

    return render_template(
        "manage/relations.html",
        admin_unit=admin_unit,
    )


@app.route("/manage/admin_unit/<int:id>/organization-invitations")
@app.route("/manage/admin_unit/<int:id>/organization-invitations/<path:path>")
@auth_required()
def manage_admin_unit_organization_invitations(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

    return render_template(
        "manage/organization_invitations.html",
        admin_unit=admin_unit,
    )


@app.route("/manage/admin_unit/<int:id>/event-lists")
@app.route("/manage/admin_unit/<int:id>/event-lists/<path:path>")
@auth_required()
def manage_admin_unit_event_lists(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

    return render_template(
        "manage/event_lists.html",
        admin_unit=admin_unit,
    )


@app.route("/manage/admin_unit/<int:id>/custom-widgets")
@app.route("/manage/admin_unit/<int:id>/custom-widgets/<path:path>")
@auth_required()
def manage_admin_unit_custom_widgets(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)
    full_height = path is not None and (path == "create" or path.endswith("/update"))

    return render_template(
        "manage/custom_widgets.html",
        admin_unit=admin_unit,
        full_height=full_height,
    )


@app.route("/manage/admin_unit/<int:id>/events/import")
@auth_required()
def manage_admin_unit_events_import(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    access_or_401(admin_unit, "event:create")
    set_current_admin_unit(admin_unit)

    return render_template(
        "manage/events_vue.html",
        admin_unit=admin_unit,
    )


@app.route("/manage/admin_unit/<int:id>/export", methods=["GET", "POST"])
@auth_required()
def manage_admin_unit_export(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "admin_unit:update"):  # pragma: no cover
        return permission_missing(url_for("manage_admin_unit", id=admin_unit.id))

    if "poll" in request.args:  # pragma: no cover
        return get_celery_poll_result()

    if request.method == "POST":  # pragma: no cover
        result = dump_admin_unit_task.delay(admin_unit.id)
        return {"result_id": result.id}

    set_current_admin_unit(admin_unit)

    file_name = f"org-{admin_unit.id}.zip"
    file_path = os.path.join(dump_org_path, file_name)
    dump_file = None

    if os.path.exists(file_path):
        dump_file = {
            "url": url_for(
                "manage_admin_unit_export_dump_files", id=admin_unit.id, path=file_name
            ),
            "size": os.path.getsize(file_path),
            "ctime": os.path.getctime(file_path),
        }

    return render_template(
        "manage/export.html",
        admin_unit=admin_unit,
        dump_file=dump_file,
    )


@app.route("/manage/admin_unit/<int:id>/export/dump/<path:path>")
def manage_admin_unit_export_dump_files(id, path):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    access_or_401(admin_unit, "admin_unit:update")

    return send_from_directory(dump_org_path, path)


@app.route("/manage/admin_unit/<int:id>/widgets", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_widgets(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

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
