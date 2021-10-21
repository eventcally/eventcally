from flask import flash, redirect, render_template, request, url_for
from flask_babelex import gettext
from flask_security import auth_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import (
    can_create_admin_unit,
    get_admin_unit_for_manage_or_404,
    get_admin_unit_members_with_permission,
    has_access,
)
from project.forms.admin_unit import CreateAdminUnitForm, UpdateAdminUnitForm
from project.models import AdminUnit, AdminUnitInvitation, AdminUnitRelation, Location
from project.services.admin_unit import (
    insert_admin_unit_for_user,
    upsert_admin_unit_relation,
)
from project.utils import strings_are_equal_ignoring_case
from project.views.utils import (
    flash_errors,
    flash_message,
    get_current_admin_unit,
    handleSqlError,
    permission_missing,
    send_mails,
)


def update_admin_unit_with_form(admin_unit, form, embedded_relation_enabled=False):
    form.populate_obj(admin_unit)


def add_relation(admin_unit, form, current_admin_unit):
    embedded_relation = form.embedded_relation.object_data

    verify = embedded_relation.verify and current_admin_unit.can_verify_other
    auto_verify_event_reference_requests = (
        embedded_relation.auto_verify_event_reference_requests
        and current_admin_unit.incoming_reference_requests_allowed
    )

    if not verify and not auto_verify_event_reference_requests:
        return

    relation = upsert_admin_unit_relation(current_admin_unit.id, admin_unit.id)
    relation.verify = verify
    relation.auto_verify_event_reference_requests = auto_verify_event_reference_requests

    db.session.commit()


@app.route("/admin_unit/create", methods=("GET", "POST"))
@auth_required()
def admin_unit_create():
    invitation = None

    invitation_id = (
        int(request.args.get("invitation_id")) if "invitation_id" in request.args else 0
    )
    if invitation_id > 0:
        invitation = AdminUnitInvitation.query.get_or_404(invitation_id)

        if not strings_are_equal_ignoring_case(invitation.email, current_user.email):
            return permission_missing(url_for("manage_admin_units"))

    if not invitation and not can_create_admin_unit():
        flash_message(
            gettext(
                "Organizations cannot currently be created. The project is in a closed test phase. If you are interested, you can contact us."
            ),
            url_for("contact"),
            gettext("Contact"),
            "danger",
        )
        return redirect(url_for("manage_admin_units"))

    form = CreateAdminUnitForm()

    if invitation and not form.is_submitted():
        form.name.data = invitation.admin_unit_name

    current_admin_unit = get_current_admin_unit()
    embedded_relation_enabled = (
        not invitation
        and current_admin_unit
        and has_access(current_admin_unit, "admin_unit:update")
        and (
            current_admin_unit.can_verify_other
            or current_admin_unit.incoming_reference_requests_allowed
        )
    )

    if embedded_relation_enabled and not form.is_submitted():
        form.embedded_relation.verify.data = True

    if form.validate_on_submit():
        admin_unit = AdminUnit()
        admin_unit.location = Location()
        update_admin_unit_with_form(admin_unit, form)

        try:
            _, _, relation = insert_admin_unit_for_user(
                admin_unit, current_user, invitation
            )

            if embedded_relation_enabled:
                add_relation(admin_unit, form, current_admin_unit)

            if invitation and relation:
                send_admin_unit_invitation_accepted_mails(
                    invitation, relation, admin_unit
                )

            if invitation:
                db.session.delete(invitation)
                db.session.commit()

            flash(gettext("Organization successfully created"), "success")
            return redirect(url_for("manage_admin_unit", id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "admin_unit/create.html",
        form=form,
        embedded_relation_enabled=embedded_relation_enabled,
    )


@app.route("/admin_unit/<int:id>/update", methods=("GET", "POST"))
@auth_required()
def admin_unit_update(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "admin_unit:update"):
        return permission_missing(url_for("manage_admin_unit", id=admin_unit.id))

    form = UpdateAdminUnitForm(obj=admin_unit)

    if form.validate_on_submit():
        update_admin_unit_with_form(admin_unit, form)

        try:
            db.session.commit()
            flash(gettext("AdminUnit successfully updated"), "success")
            return redirect(url_for("admin_unit_update", id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin_unit/update.html", form=form, admin_unit=admin_unit)


def send_admin_unit_invitation_accepted_mails(
    invitation: AdminUnitInvitation, relation: AdminUnitRelation, admin_unit: AdminUnit
):
    # Benachrichtige alle Mitglieder der AdminUnit, die diese Einladung erstellt hatte
    members = get_admin_unit_members_with_permission(
        invitation.admin_unit_id, "admin_unit:update"
    )
    emails = list(map(lambda member: member.user.email, members))

    send_mails(
        emails,
        gettext("Organization invitation accepted"),
        "organization_invitation_accepted_notice",
        invitation=invitation,
        relation=relation,
        admin_unit=admin_unit,
    )
