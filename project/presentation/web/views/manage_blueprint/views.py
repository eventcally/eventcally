from flask import abort, flash, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_security import auth_required

from project.presentation.shared.organization_create import check_organization_create
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.manage_blueprint import manage_bp
from project.presentation.web.views.utils import flash_message, permission_missing


@manage_bp.route("/organization/create", endpoint="organization_create")
@auth_required()
def organization_create():
    gate = check_organization_create(request.args.get("invitation_id", type=int))

    if gate.denial == "invitation_forbidden":
        return permission_missing(url_for("main.manage_admin_units"))

    if gate.denial == "invitation_missing":
        abort(404)

    if gate.denial == "closed":
        flash_message(
            gettext(
                "Organizations cannot currently be created. The project is in a closed test phase. If you are interested, you can contact us."
            ),
            url_for("main.contact"),
            gettext("Contact"),
            "danger",
        )
        return redirect(url_for("main.manage_admin_units"))

    if gate.denial == "deletion_requested":
        flash(gettext("Your account is scheduled for deletion."), "danger")
        return redirect(url_for("main.profile"))

    return render_template(
        "manage/organization_create.html",
        entry="manage",
        title=gettext("Create organization"),
        boot=build_boot_data(base="/"),
    )
