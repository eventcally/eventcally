from dependency_injector.wiring import Provide, inject
from flask import flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_login import current_user
from flask_security import auth_required
from flask_security.utils import get_post_login_redirect

from project.application.queries import (
    GetApiKeyQuery,
    GetOAuth2ClientQuery,
    GetUserMemberInvitationQuery,
    GetUserOAuth2TokenQuery,
    GetUserOrganizationInvitationQuery,
    GetUserOrganizationMembershipQuery,
    GetUserProfileQuery,
    ListUserOrganizationMembershipsQuery,
)
from project.application.queries.page_request import MAX_PER_PAGE, PageRequest
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.access import (
    can_current_user_delete_member,
    owner_access_or_401,
)
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.user_blueprint import user_bp


def render_user_shell(title: str):
    return render_template(
        "user/shell.html",
        entry="user",
        title=title,
        boot=build_boot_data(base="/"),
    )


@inject
def _profile(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    return result_or_404(query_bus.handle(GetUserProfileQuery(user_id=current_user.id)))


@user_bp.route("/general", endpoint="general")
@auth_required()
def general():
    return render_user_shell(gettext("General"))


@user_bp.route("/notifications", endpoint="notifications")
@auth_required()
def notifications():
    return render_user_shell(gettext("Notifications"))


@user_bp.route("/request-deletion", endpoint="request_deletion")
@auth_required()
@inject
def request_deletion(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    if _profile().deletion_requested_at:
        return redirect(url_for("user.cancel_deletion"))

    # The cap is the query bus page limit; one admin membership is enough anyway.
    memberships = query_bus.handle(
        ListUserOrganizationMembershipsQuery(
            user_id=current_user.id, page=PageRequest(per_page=MAX_PER_PAGE)
        )
    )
    if any(membership.is_admin for membership in memberships.items):
        flash(
            gettext(
                "You are administrator of at least one organization. Cancel your membership to delete your account."
            ),
            "danger",
        )
        return redirect(url_for("main.manage_admin_units"))

    return render_user_shell(gettext("Delete account"))


@user_bp.route("/cancel-deletion", endpoint="cancel_deletion")
@auth_required()
def cancel_deletion():
    if not _profile().deletion_requested_at:
        return redirect(url_for("user.request_deletion"))

    return render_user_shell(gettext("Cancel deletion"))


@user_bp.route("/accept-tos", endpoint="accept_tos")
@auth_required()
def accept_tos():
    if _profile().tos_accepted_at:
        return redirect(get_post_login_redirect())

    return render_user_shell(gettext("Confirmation required"))


# API keys


@user_bp.route("/api_keys", endpoint="api_keys")
@auth_required()
def api_keys():
    return render_user_shell(gettext("API keys"))


@user_bp.route("/api_key/create", endpoint="api_key_create")
@auth_required()
def api_key_create():
    return render_user_shell(gettext("API keys"))


@inject
def _own_api_key(
    api_key_id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    api_key = result_or_404(query_bus.handle(GetApiKeyQuery(id=api_key_id)))
    owner_access_or_401(api_key.user_id)
    return api_key


@user_bp.route("/api_key/<int:api_key_id>", endpoint="api_key")
@auth_required()
def api_key(api_key_id):
    _own_api_key(api_key_id)
    return render_user_shell(gettext("API key"))


@user_bp.route("/api_key/<int:api_key_id>/update", endpoint="api_key_update")
@auth_required()
def api_key_update(api_key_id):
    _own_api_key(api_key_id)
    return render_user_shell(gettext("API key"))


@user_bp.route("/api_key/<int:api_key_id>/delete", endpoint="api_key_delete")
@auth_required()
def api_key_delete(api_key_id):
    _own_api_key(api_key_id)
    return render_user_shell(gettext("API key"))


# OAuth2 clients


@user_bp.route("/oauth2_clients", endpoint="oauth2_clients")
@auth_required()
def oauth2_clients():
    return render_user_shell(gettext("OAuth2 clients"))


@user_bp.route("/oauth2_client/create", endpoint="oauth2_client_create")
@auth_required()
def oauth2_client_create():
    return render_user_shell(gettext("OAuth2 client"))


@inject
def _own_oauth2_client(
    oauth2_client_id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    client = result_or_404(query_bus.handle(GetOAuth2ClientQuery(id=oauth2_client_id)))
    owner_access_or_401(client.user_id)
    return client


@user_bp.route("/oauth2_client/<int:oauth2_client_id>", endpoint="oauth2_client")
@auth_required()
def oauth2_client(oauth2_client_id):
    _own_oauth2_client(oauth2_client_id)
    return render_user_shell(gettext("OAuth2 client"))


@user_bp.route(
    "/oauth2_client/<int:oauth2_client_id>/update", endpoint="oauth2_client_update"
)
@auth_required()
def oauth2_client_update(oauth2_client_id):
    _own_oauth2_client(oauth2_client_id)
    return render_user_shell(gettext("OAuth2 client"))


@user_bp.route(
    "/oauth2_client/<int:oauth2_client_id>/delete", endpoint="oauth2_client_delete"
)
@auth_required()
def oauth2_client_delete(oauth2_client_id):
    _own_oauth2_client(oauth2_client_id)
    return render_user_shell(gettext("OAuth2 client"))


# OAuth2 tokens


@user_bp.route("/oauth2_tokens", endpoint="oauth2_tokens")
@auth_required()
def oauth2_tokens():
    return render_user_shell(gettext("OAuth2 tokens"))


@user_bp.route(
    "/oauth2_token/<int:oauth2_token_id>/revoke", endpoint="oauth2_token_revoke"
)
@auth_required()
@inject
def oauth2_token_revoke(
    oauth2_token_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    token = result_or_404(query_bus.handle(GetUserOAuth2TokenQuery(id=oauth2_token_id)))

    if token.is_revoked():
        return redirect(url_for("user.oauth2_tokens"))

    return render_user_shell(gettext("OAuth2 token"))


# Memberships


@user_bp.route("/organization_members", endpoint="organization_members")
@auth_required()
def organization_members():
    return render_user_shell(gettext("Organizations"))


@user_bp.route(
    "/organization_member/<int:organization_member_id>/delete",
    endpoint="organization_member_delete",
)
@auth_required()
@inject
def organization_member_delete(
    organization_member_id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    membership = result_or_404(
        query_bus.handle(GetUserOrganizationMembershipQuery(id=organization_member_id))
    )

    if not can_current_user_delete_member(membership):
        flash(
            gettext("Last remaining administrator can not leave the organization."),
            "danger",
        )
        return redirect(
            url_for(
                "manage_admin_unit.organization_members", id=membership.admin_unit_id
            )
        )

    return render_user_shell(gettext("Leave organization"))


# Invitations


@user_bp.route(
    "/organization_member_invitations", endpoint="organization_member_invitations"
)
@auth_required()
def organization_member_invitations():
    return render_user_shell(gettext("Organization member invitations"))


@user_bp.route(
    "/organization_member_invitation/<int:organization_member_invitation_id>/negotiate",
    endpoint="organization_member_invitation_negotiate",
)
@auth_required()
@inject
def organization_member_invitation_negotiate(
    organization_member_invitation_id,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    result_or_404(
        query_bus.handle(
            GetUserMemberInvitationQuery(id=organization_member_invitation_id)
        )
    )
    return render_user_shell(gettext("Organization member invitation"))


@user_bp.route("/organization_invitations", endpoint="organization_invitations")
@auth_required()
def organization_invitations():
    return render_user_shell(gettext("Organization invitations"))


@user_bp.route(
    "/organization_invitation/<int:organization_invitation_id>/negotiate",
    endpoint="organization_invitation_negotiate",
)
@auth_required()
@inject
def organization_invitation_negotiate(
    organization_invitation_id,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    result_or_404(
        query_bus.handle(
            GetUserOrganizationInvitationQuery(id=organization_invitation_id)
        )
    )
    return render_user_shell(gettext("Organization invitation"))
