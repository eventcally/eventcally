from flask import Blueprint, g

manage_admin_unit_bp = Blueprint(
    "manage_admin_unit",
    __name__,
    url_prefix="/manage/admin_unit/<int:id>",
    template_folder="templates",
)


@manage_admin_unit_bp.url_defaults
def manage_admin_unit_url_defaults(endpoint, values):
    if "id" not in values:
        values.setdefault("id", g.manage_admin_unit.id)


@manage_admin_unit_bp.url_value_preprocessor
def manage_admin_unit_url_value_preprocessor(endpoint, values):
    from project.access import get_admin_unit_for_manage_or_404
    from project.views.utils import set_current_admin_unit

    id = values.pop("id", None)
    admin_unit_for_manage = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit_for_manage)


import project.views.manage_admin_unit.event_place.view_handler
from project import app

app.register_blueprint(manage_admin_unit_bp)