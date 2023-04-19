from flask import flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.forms.user import NotificationForm
from project.models import AdminUnitInvitation, User
from project.views.utils import get_invitation_access_result, handleSqlError


@app.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html")


@app.route("/user/notifications", methods=("GET", "POST"))
@auth_required()
def user_notifications():
    user = User.query.get_or_404(current_user.id)
    form = NotificationForm(obj=user)

    if form.validate_on_submit():
        try:
            form.populate_obj(user)
            db.session.commit()
            flash(gettext("Settings successfully updated"), "success")
            return redirect(url_for("profile"))
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            flash(handleSqlError(e), "danger")

    return render_template("user/notifications.html", form=form)


@app.route("/user/organization-invitations/<int:id>")
def user_organization_invitation(id):
    invitation = AdminUnitInvitation.query.get_or_404(id)
    result = get_invitation_access_result(invitation.email)

    if result:
        return result

    return render_template("user/organization_invitations.html")


@app.route("/user/organization-invitations")
@app.route("/user/organization-invitations/<path:path>")
@auth_required()
def user_organization_invitations(path=None):
    return render_template("user/organization_invitations.html")


@app.route("/user/favorite-events")
@auth_required()
def user_favorite_events():
    return render_template("user/favorite_events.html")
