from flask import redirect, render_template, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import auth_required

from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    DeleteShellView,
    UpdateShellView,
)
from project.presentation.web.views.utils import manage_permission_required


class UpdateWidgetView(UpdateShellView):
    """A shell: the Vue page reads and writes through `/bff/manage`."""

    permission = "widgets:write"

    def get_title(self, **kwargs):
        return lazy_gettext("Widgets")


class RequestDeletionView(DeleteShellView):
    """A shell, see `UpdateWidgetView`; the Vue page asks for the name and requests."""

    permission = "settings:write"

    def check_object_access(self, object):
        result = super().check_object_access(object)

        if result:  # pragma: no cover
            return result

        if object.deletion_requested_at:
            return redirect(url_for("manage_admin_unit.cancel_deletion", id=object.id))


class CancelDeletionView(DeleteShellView):
    """A shell, see `RequestDeletionView`."""

    permission = "settings:write"

    def check_object_access(self, object):
        result = super().check_object_access(object)

        if result:  # pragma: no cover
            return result

        if not object.deletion_requested_at:
            return redirect(
                url_for("manage_admin_unit.request_deletion", id=current_admin_unit.id)
            )

    def get_title(self, **kwargs):
        return lazy_gettext("Cancel deletion")


@manage_admin_unit_bp.route("/update")
@auth_required()
@manage_permission_required("settings:write")
def update():
    return render_template(
        "manage/organization_settings.html",
        entry="manage",
        title=gettext("Settings"),
        boot=build_boot_data(base="/"),
    )
