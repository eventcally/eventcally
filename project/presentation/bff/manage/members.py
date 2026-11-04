from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, url_for
from flask_babel import gettext
from flask_login import current_user

from project.application.commands import (
    ChangeOrganizationMemberRolesCommand,
    RemoveOrganizationMemberCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetOrganizationMemberQuery,
    ListOrganizationMemberRolesQuery,
    ListOrganizationMembersQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageMessage,
    ManagePagedListParams,
    MemberListItem,
    MemberListPage,
    MemberRole,
    MemberRolesSave,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def member_role_choices(query_bus: QueryBus) -> list[MemberRole]:
    return [
        MemberRole(name=role.name, title=gettext(role.title))
        for role in query_bus.handle(ListOrganizationMemberRolesQuery())
    ]


def check_role_names(roles: list[str], choices: list[MemberRole]) -> list[str]:
    valid = {choice.name for choice in choices}

    if any(role not in valid for role in roles):
        raise FieldValidationError(["roles"], gettext("Not a valid choice"))

    return roles


def _member_or_404(id: int, member_id: int, query_bus: QueryBus):
    _access_or_forbidden(id, "organization_members:write")

    # Do not reveal the members of other organizations: the query refuses them for
    # lack of permission on their organization.
    try:
        member = result_or_404(
            query_bus.handle(GetOrganizationMemberQuery(id=member_id))
        )
    except UnauthorizedError:
        abort(404)

    if member.admin_unit_id != id:  # pragma: no cover
        abort(404)

    return member


def _model_name() -> str:
    return gettext("Organization member")


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/members",
    query=ManagePagedListParams,
    response=MemberListPage,
    summary="List the members of the organization",
)
@inject
def list_organization_members(
    id: int,
    query: ManagePagedListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "organization_members:read")
    page = result_or_404(
        query_bus.handle(
            ListOrganizationMembersQuery(admin_unit_id=id, page=query.to_page_request())
        )
    )

    if page.is_out_of_range:
        abort(404)

    return MemberListPage(
        items=[
            MemberListItem(
                id=m.id,
                email=m.user.email,
                roles=[
                    MemberRole(name=role.name, title=gettext(role.title))
                    for role in m.roles
                ],
                is_current_user=m.user_id == current_user.id,
                leave_url=(
                    url_for(
                        "user.organization_member_delete", organization_member_id=m.id
                    )
                    if m.user_id == current_user.id
                    else None
                ),
            )
            for m in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "organization_members:write"),
        role_choices=member_role_choices(query_bus),
        can_invite=has_access(
            SimpleNamespace(id=id), "organization_member_invitations:write"
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/members/<int:member_id>",
    method="PUT",
    body=MemberRolesSave,
    response=ManageMessage,
    summary="Change the roles of a member",
)
@inject
def update_organization_member(
    id: int,
    member_id: int,
    body: MemberRolesSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _member_or_404(id, member_id, query_bus)
    check_role_names(body.roles, member_role_choices(query_bus))
    message_bus.handle_command(
        ChangeOrganizationMemberRolesCommand(
            actor=actor(), id=member_id, roles=body.roles
        )
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/members/<int:member_id>/delete",
    method="POST",
    response=ManageMessage,
    summary="Remove a member from the organization",
)
@inject
def delete_organization_member(
    id: int,
    member_id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    member = _member_or_404(id, member_id, query_bus)

    # The own membership is left on the user's own page.
    if member.user_id == current_user.id:
        raise UnauthorizedError()

    message_bus.handle_command(
        RemoveOrganizationMemberCommand(actor=actor(), id=member_id)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully deleted",
            model_display_name=_model_name(),
        )
    )
