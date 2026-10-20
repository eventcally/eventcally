from dependency_injector.wiring import Provide, inject
from flask import abort, current_app
from flask_babel import gettext
from flask_security import auth_required

from project.application.commands import DeleteUserCommand, UpdateUserRolesCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetUserForAdminQuery,
    ListRolesQuery,
    ListUsersForAdminQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.admin import bff_admin_bp
from project.presentation.bff.admin.schemas import (
    AdminRoleOption,
    AdminUserDelete,
    AdminUserDetail,
    AdminUserPage,
    AdminUserRolesUpdate,
)
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.query_results import result_or_404


@bff_route(
    bff_admin_bp,
    "/users",
    query=PageParams,
    response=AdminUserPage,
    summary="List users",
)
@auth_required("session")
@inject
def users(query: PageParams, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    page = query_bus.handle(ListUsersForAdminQuery(page=query.to_page_request()))

    if page.is_out_of_range:
        abort(404)

    return AdminUserPage.from_page(page)


@bff_route(
    bff_admin_bp,
    "/users/<int:id>",
    response=AdminUserDetail,
    summary="Get user",
)
@auth_required("session")
@inject
def user(id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    found = result_or_404(query_bus.handle(GetUserForAdminQuery(id=id)))
    roles = query_bus.handle(ListRolesQuery())

    return AdminUserDetail(
        user=found.model_dump(),
        available_roles=[
            AdminRoleOption(name=r.name, title=gettext(r.title)) for r in roles
        ],
    )


@bff_route(
    bff_admin_bp,
    "/users/<int:id>/roles",
    method="PUT",
    body=AdminUserRolesUpdate,
    summary="Update user roles",
)
@auth_required("session")
@inject
def update_user_roles(
    id: int,
    body: AdminUserRolesUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    found = result_or_404(query_bus.handle(GetUserForAdminQuery(id=id)))

    # The repository silently drops unknown role names, so reject them here.
    known = {r.name for r in query_bus.handle(ListRolesQuery())}
    if not set(body.roles) <= known:
        raise FieldValidationError(["roles"], gettext("Not a valid choice"))

    message_bus.handle_command(
        UpdateUserRolesCommand(
            actor=current_app.container.context.context_provider().current_actor,
            id=found.id,
            roles=list(dict.fromkeys(body.roles)),
        )
    )


@bff_route(
    bff_admin_bp,
    "/users/<int:id>",
    method="DELETE",
    body=AdminUserDelete,
    summary="Delete user",
)
@auth_required("session")
@inject
def delete_user(
    id: int,
    body: AdminUserDelete,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    found = result_or_404(query_bus.handle(GetUserForAdminQuery(id=id)))

    if body.email.casefold() != found.email.casefold():
        raise FieldValidationError(
            ["email"], gettext("Entered email does not match user email")
        )

    message_bus.handle_command(
        DeleteUserCommand(
            actor=current_app.container.context.context_provider().current_actor,
            id=found.id,
        )
    )
