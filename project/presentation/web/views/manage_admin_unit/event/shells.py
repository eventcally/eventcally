from flask import render_template
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetEventForEditQuery
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/event/create")
@auth_required()
@manage_permission_required("events:write")
def event_create():
    return render_manage_shell(
        gettext("Create %(model_display_name)s", model_display_name=gettext("Event"))
    )


@manage_admin_unit_bp.route("/event/<int:event_id>/update")
@auth_required()
@manage_permission_required("events:write")
def event_update(event_id):
    owned_object_or_abort(GetEventForEditQuery(id=event_id))

    return render_manage_shell(
        gettext("Update %(model_display_name)s", model_display_name=gettext("Event"))
    )


@manage_admin_unit_bp.route("/event/<int:event_id>/delete")
@auth_required()
@manage_permission_required("events:write")
def event_delete(event_id):
    owned_object_or_abort(GetEventForEditQuery(id=event_id))

    return render_manage_shell(
        gettext("Delete %(model_display_name)s", model_display_name=gettext("Event"))
    )


@manage_admin_unit_bp.route("/events")
@auth_required()
@manage_permission_required("events:read")
def events():
    return render_template(
        "manage/events.html",
        entry="manage",
        title=gettext("Events"),
        boot=build_boot_data(base="/"),
    )
