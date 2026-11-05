from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetAppQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


def _title(app):
    return app.client_name or f"{gettext('OAuth2 client')} {app.id}"


@manage_admin_unit_bp.route("/apps")
@auth_required()
@manage_permission_required("apps:read")
def apps():
    return render_manage_shell(gettext("Apps"))


@manage_admin_unit_bp.route("/app/create")
@auth_required()
@manage_permission_required("apps:write")
def app_create():
    return render_manage_shell(
        gettext("Create %(model_display_name)s", model_display_name=gettext("App"))
    )


@manage_admin_unit_bp.route("/app/<int:app_id>")
@auth_required()
@manage_permission_required("apps:read")
def app(app_id):
    return render_manage_shell(_title(owned_object_or_abort(GetAppQuery(id=app_id))))


@manage_admin_unit_bp.route("/app/<int:app_id>/update")
@auth_required()
@manage_permission_required("apps:write")
def app_update(app_id):
    owned_object_or_abort(GetAppQuery(id=app_id))
    return render_manage_shell(
        gettext("Update %(model_display_name)s", model_display_name=gettext("App"))
    )
