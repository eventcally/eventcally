from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetApiKeyQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/api_keys")
@auth_required()
@manage_permission_required("api_keys:read")
def api_keys():
    return render_manage_shell(gettext("API keys"))


@manage_admin_unit_bp.route("/api_key/create")
@auth_required()
@manage_permission_required("api_keys:write")
def api_key_create():
    return render_manage_shell(
        gettext("Create %(model_display_name)s", model_display_name=gettext("API key"))
    )


@manage_admin_unit_bp.route("/api_key/<int:api_key_id>")
@auth_required()
@manage_permission_required("api_keys:read")
def api_key(api_key_id):
    object = owned_object_or_abort(GetApiKeyQuery(id=api_key_id))

    return render_manage_shell(f"{gettext('API key')} {object.id}")
