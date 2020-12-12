from project import app, db
from project.models import AdminUnit
from flask import render_template, flash, url_for, redirect
from flask_babelex import gettext
from flask_security import roles_required
from project.forms.admin import AdminSettingsForm
from project.services.admin import upsert_settings
from project.views.utils import (
    flash_errors,
    handleSqlError,
)
from sqlalchemy.exc import SQLAlchemyError


@app.route("/admin")
@roles_required("admin")
def admin():
    return render_template("admin/admin.html")


@app.route("/admin/admin_units")
@roles_required("admin")
def admin_admin_units():
    return render_template("admin/admin_units.html", admin_units=AdminUnit.query.all())


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
