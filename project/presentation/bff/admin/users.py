from dependency_injector.wiring import Provide, inject
from flask import abort
from flask_security import auth_required

from project.application.queries import ListUsersForAdminQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.admin import bff_admin_bp
from project.presentation.bff.admin.schemas import AdminUserPage
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams


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
