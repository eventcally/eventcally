from authlib.integrations.flask_oauth2 import current_token
from flask import abort
from flask.helpers import make_response
from flask_apispec import doc, marshal_with, use_kwargs
from flask_security import current_user

from project.application.commands import DeclineOrganizationInvitationCommand
from project.application.queries import (
    GetUserOrganizationInvitationQuery,
    ListUserAppInstallationsQuery,
    ListUserOrganizationInvitationsQuery,
    ListUserOrganizationMembershipsQuery,
    OrganizationInvitationSort,
)
from project.presentation.api import add_api_resource
from project.presentation.api.organization_invitation.schemas import (
    OrganizationInvitationListRequestSchema,
    OrganizationInvitationListResponseSchema,
    OrganizationInvitationSchema,
)
from project.presentation.api.resources import BaseResource, require_api_access
from project.presentation.api.user.schemas import (
    OrganizationMembershipListRequestSchema,
    OrganizationMembershipListResponseSchema,
    UserAppInstallationListRequestSchema,
    UserAppInstallationListResponseSchema,
)
from project.presentation.shared.access import login_api_user_or_401
from project.presentation.shared.query_args import (
    enum_or_none,
    page_request_from_kwargs,
    trackable_criteria_from_kwargs,
)
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)


class UserOrganizationInvitationListResource(BaseResource):
    @doc(
        summary="List organization invitations of user",
        tags=["Users", "Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationListRequestSchema, location=("query"))
    @marshal_with(OrganizationInvitationListResponseSchema)
    @require_api_access("user.organization_invitations:read")
    def get(self, **kwargs):
        login_api_user_or_401()

        page = self.query_bus.handle(
            ListUserOrganizationInvitationsQuery(
                user_id=current_user.id,
                sort=enum_or_none(OrganizationInvitationSort, kwargs.get("sort")),
                trackable=trackable_criteria_from_kwargs(kwargs),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class UserOrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation of user",
        tags=["Users", "Organization Invitations"],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_api_access("user.organization_invitations:read")
    def get(self, id):
        login_api_user_or_401()
        return result_or_404(
            self.query_bus.handle(GetUserOrganizationInvitationQuery(id=id))
        )

    @doc(
        summary="Delete organization invitation of user",
        tags=["Users", "Organization Invitations"],
    )
    @marshal_with(None, 204)
    @require_api_access("user.organization_invitations:write")
    def delete(self, id):
        login_api_user_or_401()
        result_or_404(self.query_bus.handle(GetUserOrganizationInvitationQuery(id=id)))

        cmd = DeclineOrganizationInvitationCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


class UserOrganizationMembershipListResource(BaseResource):
    @doc(
        summary="List organization memberships of user",
        tags=["Users", "Organization Members"],
    )
    @use_kwargs(OrganizationMembershipListRequestSchema, location=("query"))
    @marshal_with(OrganizationMembershipListResponseSchema)
    @require_api_access("user.organization_memberships:read")
    def get(self, **kwargs):
        login_api_user_or_401()

        page = self.query_bus.handle(
            ListUserOrganizationMembershipsQuery(
                user_id=current_user.id, page=page_request_from_kwargs(kwargs)
            )
        )
        abort_if_page_out_of_range(page)
        return page


class UserAppInstallationListResource(BaseResource):
    @doc(
        summary="List installations of your app that the authenticated user has permission to access.",
        tags=["Users", "Apps"],
    )
    @use_kwargs(UserAppInstallationListRequestSchema, location=("query"))
    @marshal_with(UserAppInstallationListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        if not current_token or not current_token.client_id:  # pragma: no cover
            abort(401)
        login_api_user_or_401()

        page = self.query_bus.handle(
            ListUserAppInstallationsQuery(
                user_id=current_user.id,
                app_id=current_token.client.id,
                admin_only=bool(kwargs.get("admin_only", False)),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(
    UserAppInstallationListResource,
    "/user/app_installations",
    "api_v1_user_app_installation_list",
)

add_api_resource(
    UserOrganizationMembershipListResource,
    "/user/organization-memberships",
    "api_v1_user_organization_membership_list",
)


add_api_resource(
    UserOrganizationInvitationListResource,
    "/user/organization-invitations",
    "api_v1_user_organization_invitation_list",
)

add_api_resource(
    UserOrganizationInvitationResource,
    "/user/organization-invitation/<int:id>",
    "api_v1_user_organization_invitation",
)
