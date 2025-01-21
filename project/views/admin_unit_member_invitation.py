from flask import flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.forms.admin_unit_member import NegotiateAdminUnitMemberInvitationForm
from project.models import AdminUnitMemberInvitation
from project.services.admin_unit import add_user_to_admin_unit_with_roles
from project.views.utils import get_invitation_access_result, handleSqlError


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
