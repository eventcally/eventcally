from project import app, db
from project.models import AdminUnit, User, Role
from flask import render_template, flash, url_for, redirect
from flask_babelex import gettext
from flask_security import roles_required
from project.forms.admin import AdminSettingsForm, UpdateUserForm, UpdateAdminUnitForm
from project.services.admin import upsert_settings
from project.services.user import set_roles_for_user
from project.views.utils import (
    flash_errors,
    handleSqlError,
    get_pagination_urls,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func


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
            flash(gettext("Admin unit successfully updated"), "success")
            return redirect(url_for("admin_admin_units"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "admin/update_admin_unit.html", admin_unit=admin_unit, form=form
    )


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
