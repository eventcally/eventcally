from project import app, db
from project.models import AdminUnit
from flask import render_template, flash, url_for, redirect, request, jsonify
from flask_babelex import gettext
from flask_security import auth_required, roles_required
from project.access import has_access, access_or_401
from sqlalchemy.sql import asc, func


@app.route("/admin")
@roles_required("admin")
def admin():
    return render_template("admin/admin.html")


@app.route("/admin/admin_units")
@roles_required("admin")
def admin_admin_units():
    return render_template("admin/admin_units.html", admin_units=AdminUnit.query.all())
