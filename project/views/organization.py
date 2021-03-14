from flask import render_template

from project import app
from project.models import AdminUnit


@app.route("/organization/<int:id>")
def organization(id):
    organization = AdminUnit.query.get_or_404(id)

    return render_template("organization/read.html", organization=organization)
