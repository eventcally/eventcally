from flask import abort
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetAppInstallationQuery, GetInstallableAppQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    query_bus,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/app_installations")
@auth_required()
@manage_permission_required("app_installations:read")
def app_installations():
    return render_manage_shell(gettext("App installations"))


@manage_admin_unit_bp.route("/app_installation/<int:app_installation_id>")
@auth_required()
@manage_permission_required("app_installations:read")
def app_installation(app_installation_id):
    object = owned_object_or_abort(GetAppInstallationQuery(id=app_installation_id))

    return render_manage_shell(f"{gettext('App installation')} {object.id}")


@manage_admin_unit_bp.route("/app_installations/install/<int:app_id>")
@auth_required()
@manage_permission_required("app_installations:write")
def app_installations_install(app_id):
    if query_bus().handle(GetInstallableAppQuery(id=app_id)) is None:
        abort(404)

    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("App installation"),
        )
    )
