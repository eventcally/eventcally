from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project import db
from project.access import access_or_401, login_api_user_or_401
from project.api import add_api_resource
from project.api.organization_invitation.schemas import (
    OrganizationInvitationPatchRequestSchema,
    OrganizationInvitationSchema,
    OrganizationInvitationUpdateRequestSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AdminUnitInvitation


class OrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_api_access("organization.organization_invitations:read")
    def get(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        access_or_401(invitation.adminunit, "organization_invitations:read")

        return invitation

    @doc(
        summary="Update organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("organization.organization_invitations:write")
    def put(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        access_or_401(invitation.adminunit, "organization_invitations:write")

        invitation = self.update_instance(
            OrganizationInvitationUpdateRequestSchema, instance=invitation
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("organization.organization_invitations:write")
    def patch(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        access_or_401(invitation.adminunit, "organization_invitations:write")

        invitation = self.update_instance(
            OrganizationInvitationPatchRequestSchema, instance=invitation
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(None, 204)
    @require_api_access("organization.organization_invitations:write")
    def delete(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        access_or_401(invitation.adminunit, "organization_invitations:write")

        db.session.delete(invitation)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    OrganizationInvitationResource,
    "/organization-invitation/<int:id>",
    "api_v1_organization_invitation",
)
