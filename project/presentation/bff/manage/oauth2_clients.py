from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateOAuth2ClientCommand,
    DeleteOAuth2ClientCommand,
    UpdateOAuth2ClientCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetOAuth2ClientQuery,
    ListOrganizationOAuth2ClientsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageAudit,
    ManageDeleted,
    ManageNameDeleteSave,
    OAuth2ClientForm,
    OAuth2ClientListItem,
    OAuth2ClientListPage,
    OAuth2ClientRead,
    OAuth2ClientSave,
    OAuth2ClientSaved,
)
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.scopes import scopes as available_scopes
from project.shared.utils import strings_are_equal_ignoring_case


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _model_name() -> str:
    return gettext("OAuth2 client")


def _read_url(id: int, client_id: int) -> str:
    return url_for("manage_admin_unit.oauth2_client", id=id, oauth2_client_id=client_id)


def _client_or_404(id: int, client_id: int, permission: str, query_bus: QueryBus):
    _access_or_forbidden(id, permission)

    # Do not reveal the clients of other organizations or users: the query refuses
    # them for lack of permission.
    try:
        client = result_or_404(query_bus.handle(GetOAuth2ClientQuery(id=client_id)))
    except UnauthorizedError:
        abort(404)

    if client.admin_unit_id != id:
        abort(404)

    return client


def _scope_of(body: OAuth2ClientSave) -> str:
    unknown = [scope for scope in body.scopes if scope not in available_scopes]

    if unknown:
        raise FieldValidationError(
            ["scopes"], gettext("'%(value)s' is not a valid choice", value=unknown[0])
        )

    return " ".join(body.scopes)


def _redirect_uris_of(body: OAuth2ClientSave) -> list[str]:
    return [uri.strip() for uri in body.redirect_uris if uri.strip()]


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/oauth2-clients",
    query=PageParams,
    response=OAuth2ClientListPage,
    summary="List the OAuth2 clients of the organization",
)
@inject
def list_organization_oauth2_clients(
    id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "oauth2_clients:read")
    page = result_or_404(
        query_bus.handle(
            ListOrganizationOAuth2ClientsQuery(
                admin_unit_id=id, page=query.to_page_request()
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return OAuth2ClientListPage(
        items=[
            OAuth2ClientListItem(id=c.id, client_name=c.client_name) for c in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "oauth2_clients:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/oauth2-clients/form",
    response=OAuth2ClientForm,
    summary="Get the scopes an OAuth2 client of the organization can request",
)
def get_organization_oauth2_client_form(id: int):
    _access_or_forbidden(id, "oauth2_clients:write")
    return OAuth2ClientForm(scopes=list(available_scopes))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/oauth2-clients",
    method="POST",
    body=OAuth2ClientSave,
    response=OAuth2ClientSaved,
    status=201,
    summary="Create an OAuth2 client of the organization",
)
@inject
def create_organization_oauth2_client(
    id: int,
    body: OAuth2ClientSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    _access_or_forbidden(id, "oauth2_clients:write")
    result = message_bus.handle_command(
        CreateOAuth2ClientCommand(
            actor=actor(),
            name=body.client_name,
            redirect_uris=_redirect_uris_of(body),
            scope=_scope_of(body),
            admin_unit_id=id,
        )
    )
    flash(
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=_model_name(),
        ),
        "success",
    )

    return OAuth2ClientSaved(id=result.id, redirect_url=_read_url(id, result.id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/oauth2-clients/<int:client_id>",
    response=OAuth2ClientRead,
    summary="Get an OAuth2 client of the organization",
)
@inject
def get_organization_oauth2_client(
    id: int,
    client_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    client = _client_or_404(id, client_id, "oauth2_clients:read", query_bus)

    return OAuth2ClientRead(
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
        audit=ManageAudit(**client.audit.model_dump()) if client.audit else None,
        can_write=has_access(SimpleNamespace(id=id), "oauth2_clients:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/oauth2-clients/<int:client_id>",
    method="PUT",
    body=OAuth2ClientSave,
    response=OAuth2ClientSaved,
    summary="Update an OAuth2 client of the organization",
)
@inject
def update_organization_oauth2_client(
    id: int,
    client_id: int,
    body: OAuth2ClientSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _client_or_404(id, client_id, "oauth2_clients:write", query_bus)
    message_bus.handle_command(
        UpdateOAuth2ClientCommand(
            actor=actor(),
            id=client_id,
            name=body.client_name,
            redirect_uris=_redirect_uris_of(body),
            scope=_scope_of(body),
        )
    )
    flash(
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        ),
        "success",
    )

    return OAuth2ClientSaved(id=client_id, redirect_url=_read_url(id, client_id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/oauth2-clients/<int:client_id>/delete",
    method="POST",
    body=ManageNameDeleteSave,
    response=ManageDeleted,
    summary="Delete an OAuth2 client of the organization after typing its name",
)
@inject
def delete_organization_oauth2_client(
    id: int,
    client_id: int,
    body: ManageNameDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    client = _client_or_404(id, client_id, "oauth2_clients:write", query_bus)

    if not strings_are_equal_ignoring_case(body.name, client.client_name or ""):
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match OAuth2 client name")
        )

    message_bus.handle_command(DeleteOAuth2ClientCommand(actor=actor(), id=client_id))
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=_model_name(),
    )

    if not body.inline:
        flash(message, "success")

    return ManageDeleted(
        message=message, redirect_url=url_for("manage_admin_unit.oauth2_clients", id=id)
    )
