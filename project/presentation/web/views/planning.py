from flask import render_template, url_for
from flask_babel import gettext
from flask_security import auth_required

from project.presentation.shared.access import can_use_planning
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import permission_missing


@main_bp.route("/planning")
@auth_required()
def planning():
    if not can_use_planning():
        return permission_missing(url_for("main.manage_admin_units"))

    return render_template(
        "layout_vue3.html",
        entry="manage",
        title=gettext("Event Planning"),
        boot=build_boot_data(base="/"),
    )
