from flask import Blueprint, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_security import auth_required, roles_required

from project.presentation.web.boot import build_boot_data

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", defaults={"path": ""})
@admin_bp.route("/<path:path>")
@auth_required()  # anonymous users are sent to the login page
@roles_required("admin")
def shell(path):
    # Every path renders the Vue admin; its router shows unknown ones as not found.
    # Flask-Admin's static rules under /admin/flask-admin/ outrank this catch-all.
    return render_template(
        "layout_vue3.html",
        entry="admin",
        title=gettext("Admin"),
        boot=build_boot_data(base=url_for("admin.shell", path="")),
    )


# The Vue admin ran at /admin-next during the strangler; keep beta bookmarks working.
admin_next_bp = Blueprint("admin_next", __name__, url_prefix="/admin-next")


@admin_next_bp.route("/", defaults={"path": ""})
@admin_next_bp.route("/<path:path>")
def redirect_to_admin(path):
    url = url_for("admin.shell", path=path)
    if request.query_string:
        url = f"{url}?{request.query_string.decode()}"
    return redirect(url, code=301)
