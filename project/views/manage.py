import os

from flask import redirect, render_template, request, send_from_directory, url_for
from flask_security import auth_required, current_user

from project import app, dump_org_path
from project.access import (
    access_or_401,
    admin_units_the_current_user_is_member_of,
    get_admin_unit_for_manage_or_404,
    get_admin_units_for_manage,
    has_access,
)
from project.celery_tasks import dump_admin_unit_task
from project.services.admin_unit import (
    get_admin_unit_member_invitations,
    get_admin_unit_organization_invitations,
)
from project.views.utils import (
    get_celery_poll_result,
    get_current_admin_unit,
    permission_missing,
    set_current_admin_unit,
)


@app.route("/manage_after_login")
@auth_required()
def manage_after_login():
    return redirect(url_for("manage", from_login=1))


@app.route("/manage")
@auth_required()
def manage():
    admin_unit = get_current_admin_unit(False)

    if admin_unit:
        return redirect(url_for("manage_admin_unit", id=admin_unit.id))

    if "from_login" in request.args:
        admin_units = get_admin_units_for_manage()
        invitations = get_admin_unit_member_invitations(current_user.email)
        organization_invitations = get_admin_unit_organization_invitations(
            current_user.email
        )

        if (
            len(admin_units) == 1
            and len(invitations) == 0
            and len(organization_invitations) == 0
        ):
            return redirect(url_for("manage_admin_unit", id=admin_units[0].id))

        if (
            len(admin_units) == 0
            and len(invitations) == 1
            and len(organization_invitations) == 0
        ):
            return redirect(
                url_for("admin_unit_member_invitation", id=invitations[0].id)
            )

        if (
            len(admin_units) == 0
            and len(invitations) == 0
            and len(organization_invitations) == 1
        ):
            return redirect(
                url_for(
                    "user_organization_invitation", id=organization_invitations[0].id
                )
            )

    return redirect(url_for("manage_admin_units"))


@app.route("/manage/admin_units")
@auth_required()
def manage_admin_units():
    admin_units = admin_units_the_current_user_is_member_of()
    invitations = get_admin_unit_member_invitations(current_user.email)
    organization_invitations = get_admin_unit_organization_invitations(
        current_user.email
    )

    admin_units.sort(key=lambda x: x.name)
    invitations.sort(key=lambda x: x.adminunit.name)
    organization_invitations.sort(key=lambda x: x.adminunit.name)

    return render_template(
        "manage/admin_units.html",
        invitations=invitations,
        organization_invitations=organization_invitations,
        admin_units=admin_units,
    )


@app.route("/manage/admin_unit/<int:id>")
@auth_required()
def manage_admin_unit(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)
    return redirect(url_for("manage_admin_unit.events", id=admin_unit.id))


@app.route("/manage/admin_unit/<int:id>/event-lists")
@app.route("/manage/admin_unit/<int:id>/event-lists/<path:path>")
@auth_required()
def manage_admin_unit_event_lists(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)

    return render_template(
        "manage/event_lists.html",
        admin_unit=admin_unit,
    )


@app.route("/manage/admin_unit/<int:id>/custom-widgets")
@app.route("/manage/admin_unit/<int:id>/custom-widgets/<path:path>")
@auth_required()
def manage_admin_unit_custom_widgets(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)
    full_height = path is not None and (path == "create" or path.endswith("/update"))

    return render_template(
        "manage/custom_widgets.html",
        admin_unit=admin_unit,
        full_height=full_height,
    )


@app.route("/manage/admin_unit/<int:id>/export", methods=["GET", "POST"])
@auth_required()
def manage_admin_unit_export(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "admin_unit:update"):  # pragma: no cover
        return permission_missing(url_for("manage_admin_unit", id=admin_unit.id))

    if "poll" in request.args:  # pragma: no cover
        return get_celery_poll_result()

    if request.method == "POST":  # pragma: no cover
        result = dump_admin_unit_task.delay(admin_unit.id)
        return {"result_id": result.id}

    set_current_admin_unit(admin_unit)

    file_name = f"org-{admin_unit.id}.zip"
    file_path = os.path.join(dump_org_path, file_name)
    dump_file = None

    if os.path.exists(file_path):
        dump_file = {
            "url": url_for(
                "manage_admin_unit_export_dump_files", id=admin_unit.id, path=file_name
            ),
            "size": os.path.getsize(file_path),
            "ctime": os.path.getctime(file_path),
        }

    return render_template(
        "manage/export.html",
        admin_unit=admin_unit,
        dump_file=dump_file,
    )


@app.route("/manage/admin_unit/<int:id>/export/dump/<path:path>")
def manage_admin_unit_export_dump_files(id, path):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    access_or_401(admin_unit, "admin_unit:update")

    return send_from_directory(dump_org_path, path)
