from dependency_injector.wiring import Provide, inject
from flask import abort
from flask_babel import gettext
from flask_login import current_user

from project.application.commands import (
    CreateApiKeyCommand,
    DeleteApiKeyCommand,
    UpdateApiKeyCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import ApiKeySort, GetApiKeyQuery, ListUserApiKeysQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.bff.user import actor, bff_user_bp
from project.presentation.bff.user.schemas import (
    UserApiKeyCreated,
    UserApiKeyDetail,
    UserApiKeyListItem,
    UserApiKeyListParams,
    UserApiKeyPage,
    UserApiKeySave,
    UserNameConfirm,
)
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.rate_limit import rate_limit_rows
from project.shared.utils import strings_are_equal_ignoring_case


def _own_api_key(id: int, query_bus: QueryBus):
    """The query also answers an organization's key to its administrators; this area
    shows the user's own keys only."""
    api_key = result_or_404(query_bus.handle(GetApiKeyQuery(id=id)))

    if api_key.user_id != current_user.id:
        abort(403)

    return api_key


@bff_route(
    bff_user_bp,
    "/api-keys",
    query=UserApiKeyListParams,
    response=UserApiKeyPage,
    summary="List the API keys of the current user",
)
@inject
def list_api_keys(
    query: UserApiKeyListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    page = query_bus.handle(
        ListUserApiKeysQuery(
            user_id=current_user.id,
            sort=ApiKeySort(query.sort) if query.sort else None,
            page=query.to_page_request(),
        )
    )

    if page.is_out_of_range:
        abort(404)

    return UserApiKeyPage(
        items=[
            UserApiKeyListItem(id=k.id, name=k.name, created_at=k.created_at)
            for k in page.items
        ],
        **UserApiKeyPage.paging(page),
    )


@bff_route(
    bff_user_bp,
    "/api-keys",
    method="POST",
    body=UserApiKeySave,
    response=UserApiKeyCreated,
    status=201,
    summary="Create an API key; the key is only part of this answer",
)
@inject
def create_api_key(
    body: UserApiKeySave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    result = message_bus.handle_command(
        CreateApiKeyCommand(actor=actor(), name=body.name, user_id=current_user.id)
    )
    return UserApiKeyCreated(id=result.id, key=result.key)


@bff_route(
    bff_user_bp,
    "/api-keys/<int:id>",
    response=UserApiKeyDetail,
    summary="Get an API key of the current user",
)
@inject
def get_api_key(id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    api_key = _own_api_key(id, query_bus)
    return UserApiKeyDetail(
        id=api_key.id,
        name=api_key.name,
        created_at=api_key.created_at,
        rate_limits=rate_limit_rows(api_key),
        audit=api_key.audit.model_dump() if api_key.audit else None,
    )


@bff_route(
    bff_user_bp,
    "/api-keys/<int:id>",
    method="PUT",
    body=UserApiKeySave,
    summary="Rename an API key of the current user",
)
@inject
def update_api_key(
    id: int,
    body: UserApiKeySave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _own_api_key(id, query_bus)
    message_bus.handle_command(
        UpdateApiKeyCommand(actor=actor(), id=id, name=body.name)
    )


@bff_route(
    bff_user_bp,
    "/api-keys/<int:id>/delete",
    method="POST",
    body=UserNameConfirm,
    summary="Delete an API key of the current user after typing its name",
)
@inject
def delete_api_key(
    id: int,
    body: UserNameConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    api_key = _own_api_key(id, query_bus)

    if not strings_are_equal_ignoring_case(body.name, api_key.name):
        raise FieldValidationError(
            ["name"],
            gettext(
                "Entered %(property_name)s does not match %(model_display_name)s %(property_name)s",
                model_display_name=gettext("API key"),
                property_name=gettext("Name"),
            ),
        )

    message_bus.handle_command(DeleteApiKeyCommand(actor=actor(), id=id))
