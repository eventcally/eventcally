from flask import flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import get_admin_unit_for_manage_or_404, has_access
from project.forms.admin_unit_member import (
    DeleteAdminUnitInvitationForm,
    InviteAdminUnitMemberForm,
    NegotiateAdminUnitMemberInvitationForm,
)
from project.models import AdminUnitMemberInvitation, AdminUnitMemberRole
from project.services.admin_unit import add_user_to_admin_unit_with_roles
from project.views.utils import (
    flash_errors,
    get_invitation_access_result,
    handleSqlError,
    non_match_for_deletion,
    permission_missing,
    send_mail_async,
)


@app.route("/invitations/<int:id>", methods=("GET", "POST"))
def admin_unit_member_invitation(id):
    invitation = AdminUnitMemberInvitation.query.get_or_404(id)
    result = get_invitation_access_result(invitation.email)

    if result:
        return result

    form = NegotiateAdminUnitMemberInvitationForm()

    if form.validate_on_submit():
        try:
            if form.accept.data:
                if current_user.deletion_requested_at:  # pragma: no cover
                    flash(gettext("Your account is scheduled for deletion."), "danger")
                    return redirect(url_for("profile"))

                message = gettext("Invitation successfully accepted")
                roles = invitation.roles.split(",")
                add_user_to_admin_unit_with_roles(
                    current_user, invitation.adminunit, roles
                )
                url = url_for("manage_admin_unit", id=invitation.admin_unit_id)
            else:
                message = gettext("Invitation successfully declined")
                url = url_for("manage")

            db.session.delete(invitation)
            db.session.commit()
            flash(message, "success")
            return redirect(url)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")

    return render_template("invitation/read.html", form=form, invitation=invitation)


@app.route("/manage/admin_unit/<int:id>/members/invite", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_member_invite(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "admin_unit.members:invite"):
        return permission_missing(url_for("manage_admin_unit", id=admin_unit.id))

    form = InviteAdminUnitMemberForm()
    form.roles.choices = [
        (c.name, gettext(c.title))
        for c in AdminUnitMemberRole.query.order_by(AdminUnitMemberRole.id).all()
    ]

    if form.validate_on_submit():
        invitation = AdminUnitMemberInvitation()
        invitation.admin_unit_id = admin_unit.id
        form.populate_obj(invitation)
        invitation.roles = ",".join(form.roles.data)

        try:
            db.session.add(invitation)
            db.session.commit()

            send_mail_async(
                invitation.email,
                gettext("You have received an invitation"),
                "invitation_notice",
                invitation=invitation,
            )

            flash(gettext("Invitation successfully sent"), "success")
            return redirect(url_for("manage_admin_unit_members", id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    return render_template(
        "admin_unit/invite_member.html", admin_unit=admin_unit, form=form
    )


@app.route("/manage/invitation/<int:id>/delete", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_invitation_delete(id):
    invitation = AdminUnitMemberInvitation.query.get_or_404(id)
    admin_unit = invitation.adminunit

    if not has_access(admin_unit, "admin_unit.members:invite"):
        return permission_missing(url_for("manage_admin_unit", id=id))

    form = DeleteAdminUnitInvitationForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.email.data, invitation.email):
            flash(gettext("Entered email does not match invitation email"), "danger")
        else:
            try:
                db.session.delete(invitation)
                db.session.commit()
                flash(gettext("Invitation successfully deleted"), "success")
                return redirect(url_for("manage_admin_unit_members", id=admin_unit.id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "manage/delete_invitation.html", form=form, invitation=invitation
    )
