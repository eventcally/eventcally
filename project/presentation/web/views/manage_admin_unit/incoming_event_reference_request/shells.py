from flask import redirect, url_for
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetIncomingEventReferenceRequestReviewQuery
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import (
    flash_message,
    manage_permission_required,
)


@manage_admin_unit_bp.route("/incoming_event_reference_requests")
@auth_required()
@manage_permission_required("incoming_event_reference_requests:read")
def incoming_event_reference_requests():
    return render_manage_shell(gettext("Incoming reference requests"))


@manage_admin_unit_bp.route(
    "/incoming_event_reference_request/<int:event_reference_request_id>/review"
)
@auth_required()
@manage_permission_required("incoming_event_reference_requests:write")
def incoming_event_reference_request_review(event_reference_request_id):
    object = owned_object_or_abort(
        GetIncomingEventReferenceRequestReviewQuery(id=event_reference_request_id)
    )
    if object.review_status == EventReferenceRequestReviewStatus.verified:
        flash_message(
            gettext("Request already verified"),
            url_for("main.event", event_id=object.event_id),
            gettext("View event"),
            "danger",
        )
        return redirect(url_for("manage_admin_unit.incoming_event_reference_requests"))

    return render_manage_shell(
        gettext(
            "Review %(model_display_name)s",
            model_display_name=gettext("Event reference request"),
        )
    )
