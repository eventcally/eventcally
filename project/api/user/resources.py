from authlib.integrations.flask_oauth2 import current_token
from flask import abort
from flask.helpers import make_response
from flask_apispec import doc, marshal_with, use_kwargs
from flask_security import current_user
from sqlalchemy import and_

from project.access import login_api_user_or_401
from project.api import add_api_resource
from project.api.organization_invitation.schemas import (
    OrganizationInvitationListRequestSchema,
    OrganizationInvitationListResponseSchema,
    OrganizationInvitationSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.api.user.schemas import (
    OrganizationMembershipListRequestSchema,
    OrganizationMembershipListResponseSchema,
    UserAppInstallationListRequestSchema,
    UserAppInstallationListResponseSchema,
)
from project.application.commands import DeclineOrganizationInvitationCommand
from project.models import AdminUnitInvitation
from project.models.admin_unit import AdminUnit, AdminUnitMember
from project.models.app import AppInstallation
from project.services.admin_unit import get_admin_unit_organization_invitations_query
from project.services.search_params import TrackableSearchParams
from project.utils import strings_are_equal_ignoring_case


def invitation_receiver_or_401(invitation: AdminUnitInvitation):
    if not strings_are_equal_ignoring_case(invitation.email, current_user.email):
        abort(401)


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

        params = TrackableSearchParams()
        params.load_from_request(**kwargs)

        query = get_admin_unit_organization_invitations_query(current_user.email)
        query = params.get_trackable_query(query, AdminUnitInvitation)
        query = params.get_trackable_order_by(query, AdminUnitInvitation)

        return query.paginate()


class UserOrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation of user",
        tags=["Users", "Organization Invitations"],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_api_access("user.organization_invitations:read")
    def get(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        invitation_receiver_or_401(invitation)

        return invitation

    @doc(
        summary="Delete organization invitation of user",
        tags=["Users", "Organization Invitations"],
    )
    @marshal_with(None, 204)
    @require_api_access("user.organization_invitations:write")
    def delete(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        invitation_receiver_or_401(invitation)

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

        query = AdminUnitMember.query.filter_by(user_id=current_user.id)
        return query.paginate()


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

        app_id = current_token.client.id
        user_id = current_user.id

        query = AppInstallation.query.join(
            AdminUnit, AdminUnit.id == AppInstallation.admin_unit_id
        ).filter(AppInstallation.oauth2_client_id == app_id)

        admin_only = "admin_only" in kwargs and kwargs.get("admin_only", False)
        if admin_only:
            query = query.filter(
                AdminUnit.members.any(
                    and_(AdminUnitMember.user_id == user_id, AdminUnitMember.is_admin)
                )
            )
        else:
            query = query.filter(
                AdminUnit.members.any(AdminUnitMember.user_id == user_id)
            )

        pagination = query.paginate()
        return pagination


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
