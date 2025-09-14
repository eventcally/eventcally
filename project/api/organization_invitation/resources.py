from flask import g
from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project import db
from project.api import add_api_resource
from project.api.organization_invitation.schemas import (
    OrganizationInvitationPatchRequestSchema,
    OrganizationInvitationSchema,
    OrganizationInvitationUpdateRequestSchema,
)
from project.api.resources import BaseResource, require_organization_api_access
from project.models import AdminUnitInvitation


class OrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation",
        tags=["Organization Invitations"],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_organization_api_access(
        "organization.organization_invitations:read", AdminUnitInvitation
    )
    def get(self, id):
        invitation = g.manage_admin_unit_instance

        return invitation

    @doc(
        summary="Update organization invitation",
        tags=["Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.organization_invitations:write", AdminUnitInvitation
    )
    def put(self, id):
        invitation = g.manage_admin_unit_instance
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
    @require_organization_api_access(
        "organization.organization_invitations:write", AdminUnitInvitation
    )
    def patch(self, id):
        invitation = g.manage_admin_unit_instance
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
    @require_organization_api_access(
        "organization.organization_invitations:write", AdminUnitInvitation
    )
    def delete(self, id):
        invitation = g.manage_admin_unit_instance
        db.session.delete(invitation)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    OrganizationInvitationResource,
    "/organization-invitation/<int:id>",
    "api_v1_organization_invitation",
)
