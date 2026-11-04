from flask import render_template
from flask_babel import gettext
from flask_security import auth_required

from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    CreateShellView,
    DeleteShellView,
    UpdateShellView,
)
from project.presentation.web.views.utils import manage_permission_required


class CreateView(CreateShellView):
    """A shell: the Vue page reads and saves through `/bff/manage`."""


class UpdateView(UpdateShellView):
    """A shell, see `CreateView`."""


class DeleteView(DeleteShellView):
    """A shell: the page asks to confirm and deletes through `/bff/manage`."""


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
