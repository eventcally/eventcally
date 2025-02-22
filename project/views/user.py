from flask import flash, redirect, render_template, url_for
from flask_security import auth_required, current_user
from flask_security.utils import get_post_login_redirect
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.forms.security import AcceptTosForm
from project.models import AdminUnitInvitation
from project.services.user import set_user_accepted_tos
from project.views.utils import (
    get_invitation_access_result,
    handleSqlError,
    send_template_mails_to_users_async,
)


@app.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html")


@app.route("/user/accept-tos", methods=("GET", "POST"))
@auth_required()
def user_accept_tos():
    form = AcceptTosForm()

    if current_user.tos_accepted_at:  # pragma: no cover
        return redirect(get_post_login_redirect())

    if form.validate_on_submit():
        try:
            set_user_accepted_tos(current_user)
            db.session.commit()
            return redirect(get_post_login_redirect())
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            flash(handleSqlError(e), "danger")

    return render_template("user/accept_tos.html", form=form)


@app.route("/user/organization-invitations/<int:id>")
def user_organization_invitation(id):
    # Endpunkt erforderlich, weil Nutzer noch nicht registriert sein können
    invitation = AdminUnitInvitation.query.get_or_404(id)
    result = get_invitation_access_result(invitation.email)

    if result:
        return result

    return redirect(
        url_for(
            "user.organization_invitation_negotiate",
            organization_invitation_id=id,
        )
    )


@app.route("/user/favorite-events")
@auth_required()
def user_favorite_events():
    return render_template("user/favorite_events.html")


def send_user_deletion_requested_mail(user):
    send_template_mails_to_users_async(
        [user],
        "user_deletion_requested_notice",
        user=user,
    )
