from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetOutgoingOrganizationVerificationRequestQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/outgoing_organization_verification_requests")
@auth_required()
@manage_permission_required("outgoing_organization_verification_requests:read")
def outgoing_organization_verification_requests():
    return render_manage_shell(gettext("Outgoing verification requests"))


@manage_admin_unit_bp.route(
    "/outgoing_organization_verification_request/<int:organization_verification_request_id>"
)
@auth_required()
@manage_permission_required("outgoing_organization_verification_requests:read")
def outgoing_organization_verification_request(organization_verification_request_id):
    object = owned_object_or_abort(
        GetOutgoingOrganizationVerificationRequestQuery(
            id=organization_verification_request_id
        ),
        lambda object: object.source_admin_unit_id,
    )

    return render_manage_shell(
        f"{gettext('Organization verification request')} {object.id}"
    )
