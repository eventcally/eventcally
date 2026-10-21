from enum import StrEnum

from dependency_injector.wiring import Provide, inject
from flask import abort, current_app
from flask_babel import gettext
from flask_security import auth_required

from project.application.commands import (
    DeleteOrganizationCommand,
    UpdateOrganizationAdminSettingsCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetOrganizationForAdminQuery,
    ListOrganizationsForAdminQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.admin import bff_admin_bp
from project.presentation.bff.admin.schemas import (
    AdminOrganizationDelete,
    AdminOrganizationDetail,
    AdminOrganizationListParams,
    AdminOrganizationPage,
    AdminOrganizationSettingUpdate,
)
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.shared.query_results import result_or_404


class OrganizationAdminSettingKey(StrEnum):
    # The values are the field names of `UpdateOrganizationAdminSettingsCommand`
    # and `AdminOrganizationDetail`.
    incoming_reference_requests_allowed = "incoming_reference_requests_allowed"
    can_create_other = "can_create_other"
    can_invite_other = "can_invite_other"
    can_verify_other = "can_verify_other"


def _detail(found) -> AdminOrganizationDetail:
    return AdminOrganizationDetail(**found.model_dump())


@bff_route(
    bff_admin_bp,
    "/organizations",
    query=AdminOrganizationListParams,
    response=AdminOrganizationPage,
    summary="List organizations",
)
@auth_required("session")
@inject
def organizations(
    query: AdminOrganizationListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    keyword = (query.keyword or "").strip() or None
    page = query_bus.handle(
        ListOrganizationsForAdminQuery(keyword=keyword, page=query.to_page_request())
    )

    if page.is_out_of_range:
        abort(404)

    return AdminOrganizationPage.from_page(page)


@bff_route(
    bff_admin_bp,
    "/organizations/<int:id>",
    response=AdminOrganizationDetail,
    summary="Get organization",
)
@auth_required("session")
@inject
def organization(id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    return _detail(result_or_404(query_bus.handle(GetOrganizationForAdminQuery(id=id))))


@bff_route(
    bff_admin_bp,
    "/organizations/<int:id>/settings/<key>",
    method="PUT",
    body=AdminOrganizationSettingUpdate,
    response=AdminOrganizationDetail,
    summary="Update organization setting",
)
@auth_required("session")
@inject
def update_organization_setting(
    id: int,
    key: str,
    body: AdminOrganizationSettingUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    try:
        field = OrganizationAdminSettingKey(key)
    except ValueError:
        abort(404)

    found = result_or_404(query_bus.handle(GetOrganizationForAdminQuery(id=id)))

    message_bus.handle_command(
        UpdateOrganizationAdminSettingsCommand(
            actor=current_app.container.context.context_provider().current_actor,
            id=found.id,
            **{field.value: body.value},
        )
    )

    return _detail(result_or_404(query_bus.handle(GetOrganizationForAdminQuery(id=id))))


@bff_route(
    bff_admin_bp,
    "/organizations/<int:id>",
    method="DELETE",
    body=AdminOrganizationDelete,
    summary="Delete organization",
)
@auth_required("session")
@inject
def delete_organization(
    id: int,
    body: AdminOrganizationDelete,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    found = result_or_404(query_bus.handle(GetOrganizationForAdminQuery(id=id)))

    if body.name.strip().casefold() != found.name.casefold():
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match organization name")
        )

    message_bus.handle_command(
        DeleteOrganizationCommand(
            actor=current_app.container.context.context_provider().current_actor,
            id=found.id,
        )
    )
