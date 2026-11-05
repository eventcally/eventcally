from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetOutgoingOrganizationRelationQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/outgoing_organization_relations")
@auth_required()
@manage_permission_required("outgoing_organization_relations:read")
def outgoing_organization_relations():
    return render_manage_shell(gettext("Outgoing organization relations"))


@manage_admin_unit_bp.route("/outgoing_organization_relation/create")
@auth_required()
@manage_permission_required("outgoing_organization_relations:write")
def outgoing_organization_relation_create():
    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("Outgoing organization relation"),
        )
    )


@manage_admin_unit_bp.route(
    "/outgoing_organization_relation/<int:organization_relation_id>/update"
)
@auth_required()
@manage_permission_required("outgoing_organization_relations:write")
def outgoing_organization_relation_update(organization_relation_id):
    owned_object_or_abort(
        GetOutgoingOrganizationRelationQuery(id=organization_relation_id),
        lambda object: object.source_admin_unit_id,
    )

    return render_manage_shell(
        gettext(
            "Update %(model_display_name)s",
            model_display_name=gettext("Outgoing organization relation"),
        )
    )
