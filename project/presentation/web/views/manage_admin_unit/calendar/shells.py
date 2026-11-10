from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetCalendarQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@manage_admin_unit_bp.route("/calendars")
@auth_required()
@manage_permission_required("calendars:read")
def calendars():
    return render_manage_shell(gettext("Calendars"))


@manage_admin_unit_bp.route("/calendar/create")
@auth_required()
@manage_permission_required("calendars:write")
def calendar_create():
    return render_manage_shell(
        gettext(
            "Create %(model_display_name)s",
            model_display_name=gettext("Calendar"),
        )
    )


@manage_admin_unit_bp.route("/calendar/<int:calendar_id>/update")
@auth_required()
@manage_permission_required("calendars:write")
def calendar_update(calendar_id):
    owned_object_or_abort(
        GetCalendarQuery(id=calendar_id), lambda calendar: calendar.admin_unit_id
    )

    return render_manage_shell(
        gettext(
            "Update %(model_display_name)s",
            model_display_name=gettext("Calendar"),
        )
    )
