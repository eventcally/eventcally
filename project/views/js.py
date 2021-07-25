import json

from flask import request
from flask_babelex import gettext

from project import app, csrf
from project.models import AdminUnit


@app.route("/js/check/organization/short_name", methods=["POST"])
def js_check_org_short_name():
    csrf.protect()

    short_name = request.form["short_name"]
    admin_unit_id = (
        int(request.form["admin_unit_id"]) if "admin_unit_id" in request.form else -1
    )
    organization = AdminUnit.query.filter(AdminUnit.short_name == short_name).first()

    if not organization or organization.id == admin_unit_id:
        return json.dumps(True)

    error = gettext("Short name is already taken")
    return json.dumps(error)
