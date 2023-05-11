import datetime

from flask import flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required, current_user
from flask_security.utils import get_post_login_redirect
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.forms.security import AcceptTosForm
from project.forms.user import (
    CancelUserDeletionForm,
    NotificationForm,
    RequestUserDeletionForm,
)
from project.models import AdminUnitInvitation, User
from project.services.user import is_user_admin_member, set_user_accepted_tos
from project.views.utils import (
    flash_errors,
    get_invitation_access_result,
    handleSqlError,
    non_match_for_deletion,
    send_mail,
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


@app.route("/user/request-deletion", methods=("GET", "POST"))
@auth_required()
def user_request_deletion():
    if current_user.deletion_requested_at:  # pragma: no cover
        return redirect(url_for("user_cancel_deletion"))

    form = None
    form = RequestUserDeletionForm()

    if is_user_admin_member(current_user):
        flash(
            gettext(
                "You are administrator of at least one organization. Cancel your membership to delete your account."
            ),
            "danger",
        )
    elif form.validate_on_submit():
        if non_match_for_deletion(form.email.data, current_user.email):
            flash(gettext("Entered email does not match your email"), "danger")
        else:
            current_user.deletion_requested_at = datetime.datetime.utcnow()

            try:
                db.session.commit()
                send_user_deletion_requested_mail(current_user)
                return redirect(url_for("profile"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("user/request_deletion.html", form=form)


@app.route("/user/cancel-deletion", methods=("GET", "POST"))
@auth_required()
def user_cancel_deletion():
    if not current_user.deletion_requested_at:  # pragma: no cover
        return redirect(url_for("user_request_deletion"))

    form = CancelUserDeletionForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.email.data, current_user.email):
            flash(gettext("Entered email does not match your email"), "danger")
        else:
            current_user.deletion_requested_at = None

            try:
                db.session.commit()
                return redirect(url_for("profile"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("user/cancel_deletion.html", form=form)


def send_user_deletion_requested_mail(user):
    send_mail(
        user.email,
        gettext("User deletion requested"),
        "user_deletion_requested_notice",
        user=user,
    )
