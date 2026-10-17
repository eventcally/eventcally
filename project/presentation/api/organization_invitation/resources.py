from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project.application.commands import RevokeOrganizationInvitationCommand
from project.application.queries import GetOrganizationInvitationQuery, ResourceKind
from project.presentation.api import add_api_resource
from project.presentation.api.organization_invitation.schemas import (
    OrganizationInvitationPatchRequestPlainSchema,
    OrganizationInvitationPatchRequestSchema,
    OrganizationInvitationPutRequestPlainSchema,
    OrganizationInvitationSchema,
    OrganizationInvitationUpdateRequestSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


class OrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_organization_api_access(
        "organization.organization_invitations:read",
        ResourceKind.organization_invitation,
    )
    def get(self, id):
        return result_or_404(
            self.query_bus.handle(GetOrganizationInvitationQuery(id=id))
        )

    @doc(
        summary="Update organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write",
        ResourceKind.organization_invitation,
    )
    def put(self, id):
        cmd = self.load_command(OrganizationInvitationPutRequestPlainSchema)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Patch organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write",
        ResourceKind.organization_invitation,
    )
    def patch(self, id):
        cmd = self.load_command(OrganizationInvitationPatchRequestPlainSchema)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Delete organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write",
        ResourceKind.organization_invitation,
    )
    def delete(self, id):
        cmd = RevokeOrganizationInvitationCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    OrganizationInvitationResource,
    "/organization-invitation/<int:id>",
    "api_v1_organization_invitation",
)
