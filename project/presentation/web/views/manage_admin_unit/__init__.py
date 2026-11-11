from flask import Blueprint, g

manage_admin_unit_bp = Blueprint(
    "manage_admin_unit",
    __name__,
    url_prefix="/manage/admin_unit/<int:id>",
    static_folder="static",
)


@manage_admin_unit_bp.url_defaults
def manage_admin_unit_url_defaults(endpoint, values):
    if "id" not in values:
        values.setdefault("id", g.manage_admin_unit.id)


@manage_admin_unit_bp.url_value_preprocessor
def manage_admin_unit_url_value_preprocessor(endpoint, values):
    from project.presentation.shared.access import get_admin_unit_for_manage_or_404
    from project.presentation.shared.current_admin_unit import set_current_admin_unit

    id = values.pop("id", None)
    admin_unit_for_manage = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit_for_manage)


import project.presentation.web.views.manage_admin_unit.admin_unit.shells
import project.presentation.web.views.manage_admin_unit.api_key.shells
import project.presentation.web.views.manage_admin_unit.app.shells
import project.presentation.web.views.manage_admin_unit.app_installation.shells
import project.presentation.web.views.manage_admin_unit.calendar.shells
import project.presentation.web.views.manage_admin_unit.event.shells
import project.presentation.web.views.manage_admin_unit.event_organizer.shells
import project.presentation.web.views.manage_admin_unit.event_place.shells
import project.presentation.web.views.manage_admin_unit.incoming_event_reference.shells
import project.presentation.web.views.manage_admin_unit.incoming_event_reference_request.shells
import project.presentation.web.views.manage_admin_unit.incoming_verification_request.shells
import project.presentation.web.views.manage_admin_unit.member.shells
import project.presentation.web.views.manage_admin_unit.member_invitation.shells
import project.presentation.web.views.manage_admin_unit.oauth2_client.shells
import project.presentation.web.views.manage_admin_unit.organization_invitation.shells
import project.presentation.web.views.manage_admin_unit.outgoing_event_reference.shells
import project.presentation.web.views.manage_admin_unit.outgoing_event_reference_request.shells
import project.presentation.web.views.manage_admin_unit.outgoing_organization_relation.shells
import project.presentation.web.views.manage_admin_unit.outgoing_verification_request.shells
