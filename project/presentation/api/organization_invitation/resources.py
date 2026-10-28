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


def _get(resource, invitation_id):
    return result_or_404(
        resource.query_bus.handle(GetOrganizationInvitationQuery(id=invitation_id))
    )


def _put(resource):
    cmd = resource.load_command(OrganizationInvitationPutRequestPlainSchema)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _patch(resource):
    cmd = resource.load_command(OrganizationInvitationPatchRequestPlainSchema)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _delete(resource, invitation_id):
    cmd = RevokeOrganizationInvitationCommand(
        id=invitation_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


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
        return _get(self, id)

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
        return _put(self)

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
        return _patch(self)

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
        return _delete(self, id)


class OrganizationOrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_organization_api_access(
        "organization.organization_invitations:read",
        ResourceKind.organization_invitation,
        item_arg="organization_invitation_id",
    )
    def get(self, id, organization_invitation_id):
        return _get(self, organization_invitation_id)

    @doc(
        summary="Update organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write",
        ResourceKind.organization_invitation,
        item_arg="organization_invitation_id",
    )
    def put(self, id, organization_invitation_id):
        return _put(self)

    @doc(
        summary="Patch organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write",
        ResourceKind.organization_invitation,
        item_arg="organization_invitation_id",
    )
    def patch(self, id, organization_invitation_id):
        return _patch(self)

    @doc(
        summary="Delete organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write",
        ResourceKind.organization_invitation,
        item_arg="organization_invitation_id",
    )
    def delete(self, id, organization_invitation_id):
        return _delete(self, organization_invitation_id)


add_api_resource(
    OrganizationInvitationResource,
    "/organization-invitation/<int:id>",
    "api_v1_organization_invitation",
    deprecated="/organizations/{id}/organization-invitations/{organization_invitation_id}",
)
add_api_resource(
    OrganizationOrganizationInvitationResource,
    "/organizations/<int:id>/organization-invitations/<int:organization_invitation_id>",
    "api_v1_organization_organization_invitation",
)
