from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetIncomingEventReferenceQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/incoming_event_references")
@auth_required()
@manage_permission_required("incoming_event_references:read")
def incoming_event_references():
    return render_manage_shell(gettext("Incoming references"))


@manage_admin_unit_bp.route("/incoming_event_reference/<int:event_reference_id>")
@auth_required()
@manage_permission_required("incoming_event_references:read")
def incoming_event_reference(event_reference_id):
    object = owned_object_or_abort(
        GetIncomingEventReferenceQuery(id=event_reference_id)
    )

    return render_manage_shell(f"{gettext('Event reference')} {object.id}")
