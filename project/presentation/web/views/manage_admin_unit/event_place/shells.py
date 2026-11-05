from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetEventPlaceForEditQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/event_places")
@auth_required()
@manage_permission_required("event_places:read")
def event_places():
    return render_manage_shell(gettext("Places"))


@manage_admin_unit_bp.route("/event_place/create")
@auth_required()
@manage_permission_required("event_places:write")
def event_place_create():
    return render_manage_shell(
        gettext("Create %(model_display_name)s", model_display_name=gettext("Place"))
    )


@manage_admin_unit_bp.route("/event_place/<int:event_place_id>/update")
@auth_required()
@manage_permission_required("event_places:write")
def event_place_update(event_place_id):
    owned_object_or_abort(GetEventPlaceForEditQuery(id=event_place_id))

    return render_manage_shell(
        gettext("Update %(model_display_name)s", model_display_name=gettext("Place"))
    )
