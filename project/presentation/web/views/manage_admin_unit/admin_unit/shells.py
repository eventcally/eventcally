from flask import redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetOrganizationSettingsQuery
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    query_bus,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


def _organization():
    return query_bus().handle(GetOrganizationSettingsQuery(id=current_admin_unit.id))


@manage_admin_unit_bp.route("/widgets")
@auth_required()
@manage_permission_required("widgets:write")
def widgets():
    return render_manage_shell(gettext("Widgets"))


@manage_admin_unit_bp.route("/request-deletion")
@auth_required()
@manage_permission_required("settings:write")
def request_deletion():
    organization = _organization()

    if organization.deletion_requested_at:
        return redirect(
            url_for("manage_admin_unit.cancel_deletion", id=organization.id)
        )

    return render_manage_shell(
        gettext(
            "Delete %(model_display_name)s",
            model_display_name=gettext("Organization"),
        )
    )


@manage_admin_unit_bp.route("/cancel-deletion")
@auth_required()
@manage_permission_required("settings:write")
def cancel_deletion():
    organization = _organization()

    if not organization.deletion_requested_at:
        return redirect(
            url_for("manage_admin_unit.request_deletion", id=current_admin_unit.id)
        )

    return render_manage_shell(gettext("Cancel deletion"))


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
