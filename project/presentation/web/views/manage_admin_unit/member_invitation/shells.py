from flask_babel import gettext
from flask_security import auth_required

from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/organization_member_invitations")
@auth_required()
@manage_permission_required("organization_member_invitations:read")
def organization_member_invitations():
    return render_manage_shell(gettext("Organization member invitations"))


@manage_admin_unit_bp.route("/organization_member_invitation/create")
@auth_required()
@manage_permission_required("organization_member_invitations:write")
def organization_member_invitation_create():
    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("Organization member invitation"),
        )
    )
