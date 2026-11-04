from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateApiKeyCommand,
    DeleteApiKeyCommand,
    UpdateApiKeyCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    ApiKeySort,
    GetApiKeyQuery,
    ListOrganizationApiKeysQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ApiKeyCreated,
    ApiKeyListItem,
    ApiKeyListPage,
    ApiKeyListParams,
    ApiKeyRead,
    ApiKeySave,
    ManageAudit,
    ManageDeleted,
    ManageMessage,
    ManageNameDeleteSave,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.rate_limit import rate_limit_rows
from project.shared.utils import strings_are_equal_ignoring_case


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _model_name() -> str:
    return gettext("API key")


def _list_url(id: int) -> str:
    return url_for("manage_admin_unit.api_keys", id=id)


def _api_key_or_404(id: int, api_key_id: int, permission: str, query_bus: QueryBus):
    _access_or_forbidden(id, permission)

    # Do not reveal the keys of other organizations or users: the query refuses them
    # for lack of permission.
    try:
        api_key = result_or_404(query_bus.handle(GetApiKeyQuery(id=api_key_id)))
    except UnauthorizedError:
        abort(404)

    if api_key.admin_unit_id != id:
        abort(404)

    return api_key


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/api-keys",
    query=ApiKeyListParams,
    response=ApiKeyListPage,
    summary="List the API keys of the organization",
)
@inject
def list_organization_api_keys(
    id: int,
    query: ApiKeyListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "api_keys:read")
    page = result_or_404(
        query_bus.handle(
            ListOrganizationApiKeysQuery(
                admin_unit_id=id,
                sort=ApiKeySort(query.sort) if query.sort else None,
                page=query.to_page_request(),
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return ApiKeyListPage(
        items=[
            ApiKeyListItem(id=k.id, name=k.name, created_at=k.created_at)
            for k in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "api_keys:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/api-keys",
    method="POST",
    body=ApiKeySave,
    response=ApiKeyCreated,
    status=201,
    summary="Create an API key; the key is only part of this answer",
)
@inject
def create_organization_api_key(
    id: int,
    body: ApiKeySave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    _access_or_forbidden(id, "api_keys:write")
    result = message_bus.handle_command(
        CreateApiKeyCommand(actor=actor(), name=body.name, admin_unit_id=id)
    )
    return ApiKeyCreated(id=result.id, key=result.key)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/api-keys/<int:api_key_id>",
    response=ApiKeyRead,
    summary="Get an API key of the organization",
)
@inject
def get_organization_api_key(
    id: int,
    api_key_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    api_key = _api_key_or_404(id, api_key_id, "api_keys:read", query_bus)

    return ApiKeyRead(
        id=api_key.id,
        name=api_key.name,
        created_at=api_key.created_at,
        rate_limits=rate_limit_rows(api_key),
        audit=ManageAudit(**api_key.audit.model_dump()) if api_key.audit else None,
        can_write=has_access(SimpleNamespace(id=id), "api_keys:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/api-keys/<int:api_key_id>",
    method="PUT",
    body=ApiKeySave,
    response=ManageMessage,
    summary="Rename an API key of the organization",
)
@inject
def update_organization_api_key(
    id: int,
    api_key_id: int,
    body: ApiKeySave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _api_key_or_404(id, api_key_id, "api_keys:write", query_bus)
    message_bus.handle_command(
        UpdateApiKeyCommand(actor=actor(), id=api_key_id, name=body.name)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/api-keys/<int:api_key_id>/delete",
    method="POST",
    body=ManageNameDeleteSave,
    response=ManageDeleted,
    summary="Delete an API key of the organization after typing its name",
)
@inject
def delete_organization_api_key(
    id: int,
    api_key_id: int,
    body: ManageNameDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    api_key = _api_key_or_404(id, api_key_id, "api_keys:write", query_bus)

    if not strings_are_equal_ignoring_case(body.name, api_key.name):
        raise FieldValidationError(
            ["name"],
            gettext(
                "Entered %(property_name)s does not match %(model_display_name)s %(property_name)s",
                model_display_name=_model_name(),
                property_name=gettext("Name"),
            ),
        )

    message_bus.handle_command(DeleteApiKeyCommand(actor=actor(), id=api_key_id))
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=_model_name(),
    )

    if not body.inline:
        flash(message, "success")

    return ManageDeleted(message=message, redirect_url=_list_url(id))
