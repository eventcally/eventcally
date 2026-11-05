from flask_babel import gettext
from flask_security import auth_required

from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/organization_members")
@auth_required()
@manage_permission_required("organization_members:read")
def organization_members():
    return render_manage_shell(gettext("Organization members"))
