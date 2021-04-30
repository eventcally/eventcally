from flask import flash, redirect, render_template, url_for
from flask_babelex import gettext
from flask_security import auth_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import get_admin_unit_for_manage_or_404, has_access
from project.forms.admin_unit import CreateAdminUnitForm, UpdateAdminUnitForm
from project.models import AdminUnit, Location
from project.services.admin_unit import insert_admin_unit_for_user
from project.views.utils import flash_errors, handleSqlError, permission_missing


def update_admin_unit_with_form(admin_unit, form):
    form.populate_obj(admin_unit)


@app.route("/admin_unit/create", methods=("GET", "POST"))
@auth_required()
def admin_unit_create():
    form = CreateAdminUnitForm()

    if form.validate_on_submit():
        admin_unit = AdminUnit()
        admin_unit.location = Location()
        update_admin_unit_with_form(admin_unit, form)

        try:
            insert_admin_unit_for_user(admin_unit, current_user)
            flash(gettext("Organization successfully created"), "success")
            return redirect(url_for("manage_admin_unit", id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin_unit/create.html", form=form)


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
