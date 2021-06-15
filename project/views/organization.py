from flask import render_template

from project import app
from project.models import AdminUnit


@app.route("/organization/<int:id>")
def organization(id):
    organization = AdminUnit.query.get_or_404(id)

    return render_template("organization/read.html", organization=organization)


@app.route("/org/<string:au_short_name>")
def organization_by_name(au_short_name):
    organization = AdminUnit.query.filter(
        AdminUnit.short_name == au_short_name
    ).first_or_404()

    return render_template("organization/read.html", organization=organization)
