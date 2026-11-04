from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    InviteUserToOrganizationCommand,
    RevokeMemberInvitationCommand,
    UpdateMemberInvitationCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetOrganizationMemberInvitationQuery,
    ListOrganizationMemberInvitationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.members import (
    check_role_names,
    member_role_choices,
)
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageMessage,
    ManagePagedListParams,
    MemberInvitationCreate,
    MemberInvitationForm,
    MemberInvitationListItem,
    MemberInvitationListPage,
    MemberInvitationSaved,
    MemberRolesSave,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _list_url(id: int) -> str:
    return url_for("manage_admin_unit.organization_member_invitations", id=id)


def _invitation_or_404(id: int, invitation_id: int, query_bus: QueryBus):
    _access_or_forbidden(id, "organization_member_invitations:write")

    # Do not reveal the invitations of other organizations: the query refuses them for
    # lack of permission on their organization.
    try:
        invitation = result_or_404(
            query_bus.handle(GetOrganizationMemberInvitationQuery(id=invitation_id))
        )
    except UnauthorizedError:
        abort(404)

    if invitation.admin_unit_id != id:  # pragma: no cover
        abort(404)

    return invitation


def _model_name() -> str:
    return gettext("Organization member invitation")


def _role_names(roles: str | None) -> list[str]:
    return roles.split(",") if roles else []


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/member-invitations",
    query=ManagePagedListParams,
    response=MemberInvitationListPage,
    summary="List the member invitations of the organization",
)
@inject
def list_member_invitations(
    id: int,
    query: ManagePagedListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "organization_member_invitations:read")
    page = result_or_404(
        query_bus.handle(
            ListOrganizationMemberInvitationsQuery(
                admin_unit_id=id, page=query.to_page_request()
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return MemberInvitationListPage(
        items=[
            MemberInvitationListItem(id=i.id, email=i.email, roles=_role_names(i.roles))
            for i in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(
            SimpleNamespace(id=id), "organization_member_invitations:write"
        ),
        role_choices=member_role_choices(query_bus),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/member-invitations/create-form",
    response=MemberInvitationForm,
    summary="Get the form to invite a user to the organization",
)
@inject
def get_member_invitation_create_form(
    id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "organization_member_invitations:write")

    return MemberInvitationForm(
        role_choices=member_role_choices(query_bus), list_url=_list_url(id)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/member-invitations",
    method="POST",
    body=MemberInvitationCreate,
    response=MemberInvitationSaved,
    status=201,
    summary="Invite a user to the organization",
)
@inject
def create_member_invitation(
    id: int,
    body: MemberInvitationCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "organization_member_invitations:write")
    check_role_names(body.roles, member_role_choices(query_bus))
    result = message_bus.handle_command(
        InviteUserToOrganizationCommand(
            actor=actor(), admin_unit_id=id, email=body.email, roles=body.roles
        )
    )
    flash(
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=_model_name(),
        ),
        "success",
    )

    return MemberInvitationSaved(id=result.id, redirect_url=_list_url(id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/member-invitations/<int:invitation_id>",
    method="PUT",
    body=MemberRolesSave,
    response=ManageMessage,
    summary="Change the roles of a member invitation",
)
@inject
def update_member_invitation(
    id: int,
    invitation_id: int,
    body: MemberRolesSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _invitation_or_404(id, invitation_id, query_bus)
    check_role_names(body.roles, member_role_choices(query_bus))
    message_bus.handle_command(
        UpdateMemberInvitationCommand(actor=actor(), id=invitation_id, roles=body.roles)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/member-invitations/<int:invitation_id>/delete",
    method="POST",
    response=ManageMessage,
    summary="Revoke a member invitation",
)
@inject
def delete_member_invitation(
    id: int,
    invitation_id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _invitation_or_404(id, invitation_id, query_bus)
    message_bus.handle_command(
        RevokeMemberInvitationCommand(actor=actor(), id=invitation_id)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully deleted",
            model_display_name=_model_name(),
        )
    )
