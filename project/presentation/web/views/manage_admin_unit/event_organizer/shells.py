from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetEventOrganizerForEditQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/event_organizers")
@auth_required()
@manage_permission_required("event_organizers:read")
def event_organizers():
    return render_manage_shell(gettext("Event organizers"))


@manage_admin_unit_bp.route("/event_organizer/create")
@auth_required()
@manage_permission_required("event_organizers:write")
def event_organizer_create():
    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("Event organizer"),
        )
    )


@manage_admin_unit_bp.route("/event_organizer/<int:event_organizer_id>/update")
@auth_required()
@manage_permission_required("event_organizers:write")
def event_organizer_update(event_organizer_id):
    owned_object_or_abort(GetEventOrganizerForEditQuery(id=event_organizer_id))

    return render_manage_shell(
        gettext(
            "Update %(model_display_name)s",
            model_display_name=gettext("Event organizer"),
        )
    )
