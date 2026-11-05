from flask import abort
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import (
    GetEventDetailQuery,
    GetOutgoingEventReferenceRequestQuery,
)
from project.presentation.shared.access import can_request_event_reference
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    query_bus,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/outgoing_event_reference_requests")
@auth_required()
@manage_permission_required("outgoing_event_reference_requests:read")
def outgoing_event_reference_requests():
    return render_manage_shell(gettext("Outgoing reference requests"))


@manage_admin_unit_bp.route(
    "/outgoing_event_reference_request/<int:event_reference_request_id>"
)
@auth_required()
@manage_permission_required("outgoing_event_reference_requests:read")
def outgoing_event_reference_request(event_reference_request_id):
    object = owned_object_or_abort(
        GetOutgoingEventReferenceRequestQuery(id=event_reference_request_id),
        lambda object: object.event.admin_unit.id,
    )

    return render_manage_shell(f"{gettext('Event reference request')} {object.id}")


@manage_admin_unit_bp.route(
    "/outgoing_event_reference_request/create_for_event/<int:event_id>"
)
@auth_required()
@manage_permission_required("outgoing_event_reference_requests:write")
def outgoing_event_reference_request_create_for_event(event_id):
    event = result_or_404(query_bus().handle(GetEventDetailQuery(id=event_id)))

    if not can_request_event_reference(event):
        abort(401)

    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("Event reference request"),
        )
    )
