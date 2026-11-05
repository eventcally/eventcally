from flask import redirect, url_for
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import (
    GetIncomingOrganizationVerificationRequestReviewQuery,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
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


@manage_admin_unit_bp.route("/incoming_organization_verification_requests")
@auth_required()
@manage_permission_required("incoming_organization_verification_requests:read")
def incoming_organization_verification_requests():
    return render_manage_shell(gettext("Incoming verification requests"))


@manage_admin_unit_bp.route(
    "/incoming_organization_verification_request/<int:organization_verification_request_id>/review"
)
@auth_required()
@manage_permission_required("incoming_organization_verification_requests:write")
def incoming_organization_verification_request_review(
    organization_verification_request_id,
):
    object = owned_object_or_abort(
        GetIncomingOrganizationVerificationRequestReviewQuery(
            id=organization_verification_request_id
        ),
        lambda object: object.target_admin_unit_id,
    )
    if object.review_status == OrganizationVerificationRequestReviewStatus.verified:
        flash_message(
            gettext("Verification request already verified"),
            url_for("main.organization", id=object.source_admin_unit_id),
            gettext("View organization"),
            "danger",
        )
        return redirect(
            url_for("manage_admin_unit.incoming_organization_verification_requests")
        )

    return render_manage_shell(
        gettext(
            "Review %(model_display_name)s",
            model_display_name=gettext("Organization verification request"),
        )
    )
