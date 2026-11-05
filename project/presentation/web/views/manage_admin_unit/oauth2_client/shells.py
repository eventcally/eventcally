from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetOAuth2ClientQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/oauth2_clients")
@auth_required()
@manage_permission_required("oauth2_clients:read")
def oauth2_clients():
    return render_manage_shell(gettext("OAuth2 clients"))


@manage_admin_unit_bp.route("/oauth2_client/create")
@auth_required()
@manage_permission_required("oauth2_clients:write")
def oauth2_client_create():
    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s", model_display_name=gettext("OAuth2 client")
        )
    )


@manage_admin_unit_bp.route("/oauth2_client/<int:oauth2_client_id>")
@auth_required()
@manage_permission_required("oauth2_clients:read")
def oauth2_client(oauth2_client_id):
    object = owned_object_or_abort(GetOAuth2ClientQuery(id=oauth2_client_id))

    return render_manage_shell(
        object.client_name or f"{gettext('OAuth2 client')} {object.id}"
    )


@manage_admin_unit_bp.route("/oauth2_client/<int:oauth2_client_id>/update")
@auth_required()
@manage_permission_required("oauth2_clients:write")
def oauth2_client_update(oauth2_client_id):
    owned_object_or_abort(GetOAuth2ClientQuery(id=oauth2_client_id))

    return render_manage_shell(
        gettext(
            "Update %(model_display_name)s", model_display_name=gettext("OAuth2 client")
        )
    )
