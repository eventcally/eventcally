from flask import Blueprint, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required, roles_required

from project.presentation.web.boot import build_boot_data

admin_next_bp = Blueprint("admin_next", __name__, url_prefix="/admin-next")


@admin_next_bp.route("/", defaults={"path": ""})
@admin_next_bp.route("/<path:path>")
@auth_required()  # anonymous users are sent to the login page
@roles_required("admin")
def shell(path):
    return render_template(
        "layout_vue3.html",
        entry="admin",
        title=gettext("Admin"),
        boot=build_boot_data(base=url_for("admin_next.shell", path="")),
    )
