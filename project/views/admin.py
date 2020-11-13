from project import app
from project.models import AdminUnit
from flask import render_template
from flask_security import roles_required


@app.route("/admin")
@roles_required("admin")
def admin():
    return render_template("admin/admin.html")


@app.route("/admin/admin_units")
@roles_required("admin")
def admin_admin_units():
    return render_template("admin/admin_units.html", admin_units=AdminUnit.query.all())
