from dependency_injector.wiring import Provide, inject
from flask import abort
from flask_babel import gettext
from flask_login import current_user

from project.application.commands import (
    CreateOAuth2ClientCommand,
    DeleteOAuth2ClientCommand,
    UpdateOAuth2ClientCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import GetOAuth2ClientQuery, ListUserOAuth2ClientsQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.bff.user import actor, bff_user_bp
from project.presentation.bff.user.schemas import (
    UserNameConfirm,
    UserOAuth2ClientCreated,
    UserOAuth2ClientDetail,
    UserOAuth2ClientForm,
    UserOAuth2ClientListItem,
    UserOAuth2ClientPage,
    UserOAuth2ClientSave,
)
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.scopes import scopes as available_scopes
from project.shared.utils import strings_are_equal_ignoring_case


def _own_client(id: int, query_bus: QueryBus):
    """The query also answers an organization's client to its administrators; this
    area shows the user's own clients only."""
    client = result_or_404(query_bus.handle(GetOAuth2ClientQuery(id=id)))

    if client.user_id != current_user.id:
        abort(403)

    return client


def _scope_of(body: UserOAuth2ClientSave) -> str:
    unknown = [scope for scope in body.scopes if scope not in available_scopes]

    if unknown:
        raise FieldValidationError(
            ["scopes"], gettext("'%(value)s' is not a valid choice", value=unknown[0])
        )

    return " ".join(body.scopes)


def _redirect_uris_of(body: UserOAuth2ClientSave) -> list[str]:
    return [uri.strip() for uri in body.redirect_uris if uri.strip()]


@bff_route(
    bff_user_bp,
    "/oauth2-clients",
    query=PageParams,
    response=UserOAuth2ClientPage,
    summary="List the OAuth2 clients of the current user",
)
@inject
def list_oauth2_clients(
    query: PageParams, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    page = query_bus.handle(
        ListUserOAuth2ClientsQuery(
            user_id=current_user.id, page=query.to_page_request()
        )
    )

    if page.is_out_of_range:
        abort(404)

    return UserOAuth2ClientPage(
        items=[
            UserOAuth2ClientListItem(id=c.id, client_name=c.client_name)
            for c in page.items
        ],
        **UserOAuth2ClientPage.paging(page),
    )


@bff_route(
    bff_user_bp,
    "/oauth2-clients/form",
    response=UserOAuth2ClientForm,
    summary="Get the scopes an OAuth2 client can request",
)
def get_oauth2_client_form():
    return UserOAuth2ClientForm(scopes=list(available_scopes))


@bff_route(
    bff_user_bp,
    "/oauth2-clients",
    method="POST",
    body=UserOAuth2ClientSave,
    response=UserOAuth2ClientCreated,
    status=201,
    summary="Create an OAuth2 client",
)
@inject
def create_oauth2_client(
    body: UserOAuth2ClientSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    result = message_bus.handle_command(
        CreateOAuth2ClientCommand(
            actor=actor(),
            name=body.client_name,
            redirect_uris=_redirect_uris_of(body),
            scope=_scope_of(body),
            user_id=current_user.id,
        )
    )
    return UserOAuth2ClientCreated(id=result.id)


@bff_route(
    bff_user_bp,
    "/oauth2-clients/<int:id>",
    response=UserOAuth2ClientDetail,
    summary="Get an OAuth2 client of the current user",
)
@inject
def get_oauth2_client(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    client = _own_client(id, query_bus)
    return UserOAuth2ClientDetail(
        id=client.id,
        client_id=client.client_id,
        client_secret=client.client_secret,
        client_name=client.client_name,
        client_uri=client.client_uri,
        scope=client.scope,
        scopes=[scope for scope in client.scope.split(" ") if scope],
        redirect_uris=client.redirect_uris,
        grant_types=client.grant_types,
        response_types=client.response_types,
        token_endpoint_auth_method=client.token_endpoint_auth_method,
        audit=client.audit.model_dump() if client.audit else None,
    )


@bff_route(
    bff_user_bp,
    "/oauth2-clients/<int:id>",
    method="PUT",
    body=UserOAuth2ClientSave,
    summary="Update an OAuth2 client of the current user",
)
@inject
def update_oauth2_client(
    id: int,
    body: UserOAuth2ClientSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _own_client(id, query_bus)
    message_bus.handle_command(
        UpdateOAuth2ClientCommand(
            actor=actor(),
            id=id,
            name=body.client_name,
            redirect_uris=_redirect_uris_of(body),
            scope=_scope_of(body),
        )
    )


@bff_route(
    bff_user_bp,
    "/oauth2-clients/<int:id>/delete",
    method="POST",
    body=UserNameConfirm,
    summary="Delete an OAuth2 client of the current user after typing its name",
)
@inject
def delete_oauth2_client(
    id: int,
    body: UserNameConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    client = _own_client(id, query_bus)

    if not strings_are_equal_ignoring_case(body.name, client.client_name):
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match OAuth2 client name")
        )

    message_bus.handle_command(DeleteOAuth2ClientCommand(actor=actor(), id=id))
