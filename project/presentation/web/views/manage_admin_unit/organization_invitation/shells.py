from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetOrganizationInvitationQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/organization_invitations")
@auth_required()
@manage_permission_required("organization_invitations:read")
def organization_invitations():
    return render_manage_shell(gettext("Organization invitations"))


@manage_admin_unit_bp.route("/organization_invitation/create")
@auth_required()
@manage_permission_required("organization_invitations:write")
def organization_invitation_create():
    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("Organization invitation"),
        )
    )


@manage_admin_unit_bp.route(
    "/organization_invitation/<int:organization_invitation_id>/update"
)
@auth_required()
@manage_permission_required("organization_invitations:write")
def organization_invitation_update(organization_invitation_id):
    owned_object_or_abort(GetOrganizationInvitationQuery(id=organization_invitation_id))

    return render_manage_shell(
        gettext(
            "Update %(model_display_name)s",
            model_display_name=gettext("Organization invitation"),
        )
    )
