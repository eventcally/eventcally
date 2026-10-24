from flask import (
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_babel import gettext
from flask_security import auth_required, current_user

from project.application.queries import (
    ListUserMemberInvitationsQuery,
    ListUserOrganizationInvitationsQuery,
)
from project.application.queries.page_request import MAX_PER_PAGE, PageRequest
from project.presentation.shared.access import (
    access_or_401,
    admin_units_the_current_user_is_member_of,
    get_admin_unit_for_manage_or_404,
    get_admin_units_for_manage,
    has_access,
)
from project.presentation.shared.current_admin_unit import (
    get_current_admin_unit,
    set_current_admin_unit,
)
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import permission_missing
from project.shared.paths import dump_org_path


def _get_invitations():
    # A user is not realistically invited more often than one page holds; the cap is
    # the query bus page limit.
    query_bus = current_app.container.cqrs.query_bus()
    page = PageRequest(per_page=MAX_PER_PAGE)
    invitations = query_bus.handle(
        ListUserMemberInvitationsQuery(user_id=current_user.id, page=page)
    ).items
    organization_invitations = query_bus.handle(
        ListUserOrganizationInvitationsQuery(user_id=current_user.id, page=page)
    ).items
    return list(invitations), list(organization_invitations)


@main_bp.route("/manage_after_login")
@auth_required()
def manage_after_login():
    return redirect(url_for("main.manage", from_login=1))


@main_bp.route("/manage")
@auth_required()
def manage():
    admin_unit = get_current_admin_unit(False)

    if admin_unit:
        return redirect(url_for("main.manage_admin_unit", id=admin_unit.id))

    if "from_login" in request.args:
        admin_units = get_admin_units_for_manage()
        invitations, organization_invitations = _get_invitations()

        if (
            len(admin_units) == 1
            and len(invitations) == 0
            and len(organization_invitations) == 0
        ):
            return redirect(url_for("main.manage_admin_unit", id=admin_units[0].id))

        if (
            len(admin_units) == 0
            and len(invitations) == 1
            and len(organization_invitations) == 0
        ):
            return redirect(
                url_for("main.admin_unit_member_invitation", id=invitations[0].id)
            )

        if (
            len(admin_units) == 0
            and len(invitations) == 0
            and len(organization_invitations) == 1
        ):
            return redirect(
                url_for(
                    "main.user_organization_invitation",
                    id=organization_invitations[0].id,
                )
            )

    return redirect(url_for("main.manage_admin_units"))


@main_bp.route("/manage/admin_units")
@auth_required()
def manage_admin_units():
    admin_units = admin_units_the_current_user_is_member_of()
    invitations, organization_invitations = _get_invitations()

    admin_units.sort(key=lambda x: x.name)
    invitations.sort(key=lambda x: x.admin_unit.name)
    organization_invitations.sort(key=lambda x: x.admin_unit_name)

    return render_template(
        "manage/admin_units.html",
        invitations=invitations,
        organization_invitations=organization_invitations,
        admin_units=admin_units,
    )


@main_bp.route("/manage/admin_unit/<int:id>")
@auth_required()
def manage_admin_unit(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    set_current_admin_unit(admin_unit)
    return redirect(url_for("manage_admin_unit.events", id=admin_unit.id))


@main_bp.route("/manage/admin_unit/<int:id>/custom-widgets")
@main_bp.route("/manage/admin_unit/<int:id>/custom-widgets/<path:path>")
@auth_required()
def manage_admin_unit_custom_widgets(id, path=None):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "custom_widgets:read"):  # pragma: no cover
        return permission_missing(url_for("main.manage_admin_unit", id=admin_unit.id))

    set_current_admin_unit(admin_unit)
    full_height = path is not None and (path == "create" or path.endswith("/update"))

    return render_template(
        "manage/custom_widgets.html",
        entry="manage",
        title=gettext("Custom widgets"),
        boot=build_boot_data(base="/"),
        admin_unit=admin_unit,
        full_height=full_height,
    )


@main_bp.route("/manage/admin_unit/<int:id>/export")
@auth_required()
def manage_admin_unit_export(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, "export:read"):  # pragma: no cover
        return permission_missing(url_for("main.manage_admin_unit", id=admin_unit.id))

    set_current_admin_unit(admin_unit)

    return render_template(
        "manage/export.html",
        entry="manage",
        title=gettext("Export"),
        boot=build_boot_data(base="/"),
        admin_unit=admin_unit,
    )


@main_bp.route("/manage/admin_unit/<int:id>/export/dump/<path:path>")
def manage_admin_unit_export_dump_files(id, path):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    access_or_401(admin_unit, "export:read")

    return send_from_directory(dump_org_path, path)


# Legacy mail redirects


@main_bp.route(
    "/manage/admin_unit/<int:id>/incoming_admin_unit_verification_request/<int:admin_unit_verification_request_id>/review"
)
def manage_admin_unit_incoming_admin_unit_verification_request_review(
    id, admin_unit_verification_request_id
):
    return redirect(
        url_for(
            "manage_admin_unit.incoming_organization_verification_request_review",
            id=id,
            organization_verification_request_id=admin_unit_verification_request_id,
        )
    )


@main_bp.route(
    "/manage/admin_unit/<int:id>/outgoing_admin_unit_verification_request/<int:admin_unit_verification_request_id>"
)
def manage_admin_unit_outgoing_admin_unit_verification_request(
    id, admin_unit_verification_request_id
):
    return redirect(
        url_for(
            "manage_admin_unit.outgoing_organization_verification_request",
            id=id,
            organization_verification_request_id=admin_unit_verification_request_id,
        )
    )
