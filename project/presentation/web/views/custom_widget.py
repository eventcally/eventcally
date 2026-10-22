from flask import abort, render_template

from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.main_blueprint import main_bp

WIDGET_TYPES = ("search", "calendar")


# The endpoint name is exempt from X-Frame-Options (requests.py): customers embed it.
@main_bp.route("/custom_widget/<string:type>")
def custom_widget_type(type: str):
    if type not in WIDGET_TYPES:
        abort(404)

    return render_template("custom_widget/widget.html", boot=build_boot_data(base="/"))
