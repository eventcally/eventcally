from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_security import roles_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func

from project import app, db
from project.forms.admin import (
    AdminNewsletterForm,
    AdminSettingsForm,
    AdminTestEmailForm,
    DeleteAdminUnitForm,
    DeleteUserForm,
    ResetTosAceptedForm,
    UpdateAdminUnitForm,
    UpdateUserForm,
)
from project.models import AdminUnit, Role, User
from project.services.admin import upsert_settings
from project.services.admin_unit import delete_admin_unit
from project.services.user import delete_user, set_roles_for_user
from project.views.utils import (
    flash_errors,
    get_celery_poll_group_result,
    get_pagination_urls,
    handleSqlError,
    non_match_for_deletion,
    send_mail,
    send_mail_async,
    send_mails_async,
)


@app.route("/admin")
@roles_required("admin")
def admin():
    return render_template("admin/admin.html")


@app.route("/admin/admin_units")
@roles_required("admin")
def admin_admin_units():
    admin_units = AdminUnit.query.order_by(func.lower(AdminUnit.name)).paginate()
    return render_template(
        "admin/admin_units.html",
        admin_units=admin_units.items,
        pagination=get_pagination_urls(admin_units),
    )


@app.route("/admin/admin_unit/<int:id>/update", methods=("GET", "POST"))
@roles_required("admin")
def admin_admin_unit_update(id):
    admin_unit = AdminUnit.query.get_or_404(id)

    form = UpdateAdminUnitForm(obj=admin_unit)

    if form.validate_on_submit():
        form.populate_obj(admin_unit)

        try:
            db.session.commit()
            flash(gettext("Organization successfully updated"), "success")
            return redirect(url_for("admin_admin_units"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "admin/update_admin_unit.html", admin_unit=admin_unit, form=form
    )


@app.route("/admin/admin_unit/<int:id>/delete", methods=("GET", "POST"))
@roles_required("admin")
def admin_admin_unit_delete(id):
    admin_unit = AdminUnit.query.get_or_404(id)

    form = DeleteAdminUnitForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.name.data, admin_unit.name):
            flash(gettext("Entered name does not match organization name"), "danger")
        else:
            try:
                delete_admin_unit(admin_unit)
                flash(gettext("Organization successfully deleted"), "success")
                return redirect(url_for("admin_admin_units"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "admin/delete_admin_unit.html", form=form, admin_unit=admin_unit
    )


@app.route("/admin/reset-tos-accepted", methods=("GET", "POST"))
@roles_required("admin")
def admin_reset_tos_accepted():
    from project.services.admin import reset_tos_accepted_for_users

    form = ResetTosAceptedForm()

    if form.validate_on_submit():
        try:
            reset_tos_accepted_for_users()
            return redirect(url_for("admin"))
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/reset_tos_accepted.html", form=form)


@app.route("/admin/settings", methods=("GET", "POST"))
@roles_required("admin")
def admin_settings():
    settings = upsert_settings()
    form = AdminSettingsForm(obj=settings)

    if form.validate_on_submit():
        form.populate_obj(settings)

        try:
            db.session.commit()
            flash(gettext("Settings successfully updated"), "success")
            return redirect(url_for("admin"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/settings.html", form=form)


@app.route("/admin/email", methods=["GET", "POST"])
@roles_required("admin")
def admin_email():
    form = AdminTestEmailForm()

    if "poll" in request.args:  # pragma: no cover
        return get_celery_poll_group_result()

    if form.validate_on_submit():
        subject = gettext(
            "Test mail from %(site_name)s",
            site_name=app.config["SITE_NAME"],
        )

        if "async" in request.args:  # pragma: no cover
            result = send_mail_async(form.recipient.data, subject, "test_email")
            result.save()
            return {"result_id": result.id}

        try:
            send_mail(form.recipient.data, subject, "test_email")
            flash(gettext("Mail sent successfully"), "success")
        except Exception as e:  # pragma: no cover
            flash(str(e), "danger")
    else:  # pragma: no cover
        flash_errors(form)

    return render_template("admin/email.html", form=form)


@app.route("/admin/newsletter", methods=["GET", "POST"])
@roles_required("admin")
def admin_newsletter():
    form = AdminNewsletterForm()

    if "poll" in request.args:  # pragma: no cover
        return get_celery_poll_group_result()

    if form.validate_on_submit():
        subject = gettext(
            "Newsletter from %(site_name)s",
            site_name=app.config["SITE_NAME"],
        )

        if form.recipient_choice.data == 1:  # pragma: no cover
            recipients = [form.test_recipient.data]
        else:
            users = (
                User.query.filter(User.email != None)
                .filter(User.confirmed_at != None)
                .filter(User.newsletter_enabled)
                .all()
            )
            recipients = [u.email for u in users]

        result = send_mails_async(
            recipients, subject, "newsletter", message=form.message.data
        )
        result.save()
        return {"result_id": result.id}

    return render_template("admin/newsletter.html", form=form)


@app.route("/admin/users")
@roles_required("admin")
def admin_users():
    users = User.query.order_by(func.lower(User.email)).paginate()
    return render_template(
        "admin/users.html", users=users.items, pagination=get_pagination_urls(users)
    )


@app.route("/admin/user/<int:id>/update", methods=("GET", "POST"))
@roles_required("admin")
def admin_user_update(id):
    user = User.query.get_or_404(id)

    form = UpdateUserForm()
    form.roles.choices = [
        (c.name, gettext(c.title)) for c in Role.query.order_by(Role.id).all()
    ]

    if form.validate_on_submit():
        set_roles_for_user(user.email, form.roles.data)

        try:
            db.session.commit()
            flash(gettext("User successfully updated"), "success")
            return redirect(url_for("admin_users"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        form.roles.data = [c.name for c in user.roles]

    return render_template("admin/update_user.html", user=user, form=form)


@app.route("/admin/user/<int:id>/delete", methods=("GET", "POST"))
@roles_required("admin")
def admin_user_delete(id):
    user = User.query.get_or_404(id)

    form = DeleteUserForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.email.data, user.email):
            flash(gettext("Entered email does not match user email"), "danger")
        else:
            try:
                delete_user(user)
                flash(gettext("User successfully deleted"), "success")
                return redirect(url_for("admin_users"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/delete_user.html", form=form, user=user)
