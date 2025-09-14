from flask import g

from project.modular.base_blueprint import BaseBlueprint

app_bp = BaseBlueprint(
    "app",
    __name__,
    url_prefix="/app/<int:app_id>",
    template_folder="templates",
    static_folder="static",
)


@app_bp.url_defaults
def app_bp_url_defaults(endpoint, values):
    if "app_id" not in values:
        values.setdefault("app_id", g.current_app.id)


@app_bp.url_value_preprocessor
def app_bp_url_value_preprocessor(endpoint, values):
    from project.access import admin_unit_owner_access_or_401
    from project.models import OAuth2Client

    app_id = values.pop("app_id", None)
    app = OAuth2Client.query.get_or_404(app_id)
    admin_unit_owner_access_or_401(app.admin_unit_id)
    g.current_app = app


import project.views.manage_admin_unit.app.app_key.view_handler
from project.views.manage_admin_unit import manage_admin_unit_bp

manage_admin_unit_bp.register_blueprint(app_bp)
