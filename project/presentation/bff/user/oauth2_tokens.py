from typing import Optional

from dependency_injector.wiring import Provide, inject
from flask import abort
from flask_babel import gettext
from flask_login import current_user

from project.application.commands import RevokeOAuth2TokenCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetUserOAuth2TokenQuery,
    ListUserOAuth2TokensQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.bff.user import actor, bff_user_bp
from project.presentation.bff.user.schemas import UserOAuth2Token, UserOAuth2TokenPage
from project.presentation.shared.query_results import result_or_404


def _status(token) -> Optional[str]:
    # An expired token counts as expired even if it was revoked too (as the old list did).
    if token.is_expired():
        return "expired"

    if token.is_revoked():
        return "revoked"

    return None


def _token(token) -> UserOAuth2Token:
    return UserOAuth2Token(
        id=token.id,
        client_name=token.client_name,
        scope=token.scope,
        issued_at=token.issued_at_datetime,
        expires_at=token.expires_at_datetime,
        status=_status(token),
    )


@bff_route(
    bff_user_bp,
    "/oauth2-tokens",
    query=PageParams,
    response=UserOAuth2TokenPage,
    summary="List the OAuth2 tokens of the current user",
)
@inject
def list_oauth2_tokens(
    query: PageParams, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    page = query_bus.handle(
        ListUserOAuth2TokensQuery(user_id=current_user.id, page=query.to_page_request())
    )

    if page.is_out_of_range:
        abort(404)

    return UserOAuth2TokenPage(
        items=[_token(t) for t in page.items], **UserOAuth2TokenPage.paging(page)
    )


@bff_route(
    bff_user_bp,
    "/oauth2-tokens/<int:id>",
    response=UserOAuth2Token,
    summary="Get an OAuth2 token of the current user",
)
@inject
def get_oauth2_token(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    return _token(result_or_404(query_bus.handle(GetUserOAuth2TokenQuery(id=id))))


@bff_route(
    bff_user_bp,
    "/oauth2-tokens/<int:id>/revoke",
    method="POST",
    summary="Revoke an OAuth2 token of the current user",
)
@inject
def revoke_oauth2_token(
    id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    token = result_or_404(query_bus.handle(GetUserOAuth2TokenQuery(id=id)))

    if token.is_revoked():
        abort(400, gettext("OAuth2 token is already revoked."))

    message_bus.handle_command(RevokeOAuth2TokenCommand(actor=actor(), id=id))
