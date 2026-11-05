from flask import Blueprint, current_app, g

app_bp = Blueprint(
    "app",
    __name__,
    url_prefix="/app/<int:app_id>",
    static_folder="static",
)


@app_bp.url_value_preprocessor
def app_bp_url_value_preprocessor(endpoint, values):
    from flask import abort

    from project.application.queries import GetAppQuery
    from project.presentation.shared.access import admin_unit_owner_access_or_401

    app_id = values.pop("app_id", None)
    query_bus = current_app.container.cqrs.query_bus()
    app = query_bus.handle(GetAppQuery(id=app_id))

    if app is None:
        abort(404)

    admin_unit_owner_access_or_401(app.admin_unit_id)
    g.current_app = app


import project.presentation.web.views.manage_admin_unit.app.webhook_delivery.shells
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp

manage_admin_unit_bp.register_blueprint(app_bp)
