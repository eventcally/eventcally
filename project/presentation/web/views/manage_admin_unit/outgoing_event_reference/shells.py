from flask_babel import gettext
from flask_security import auth_required

from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/outgoing_event_references")
@auth_required()
@manage_permission_required("outgoing_event_references:read")
def outgoing_event_references():
    return render_manage_shell(gettext("Outgoing references"))
