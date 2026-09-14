from flask import g, request
from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project.api import add_api_resource
from project.api.organization_relation.schemas import (
    OrganizationRelationPatchRequestPlainSchema,
    OrganizationRelationPatchRequestSchema,
    OrganizationRelationPutRequestPlainSchema,
    OrganizationRelationSchema,
    OrganizationRelationUpdateRequestSchema,
)
from project.api.resources import BaseResource, require_organization_api_access
from project.application.commands import DeleteOrganizationRelationCommand
from project.models import AdminUnitRelation


class OrganizationRelationResource(BaseResource):
    @doc(
        summary="Get organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:read",
        AdminUnitRelation,
        admin_unit_id_path="source_admin_unit_id",
    )
    def get(self, id):
        relation = g.manage_admin_unit_instance

        return relation

    @doc(
        summary="Update organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        AdminUnitRelation,
        admin_unit_id_path="source_admin_unit_id",
    )
    def put(self, id):
        cmd = OrganizationRelationPutRequestPlainSchema(
            context=g.api_command_context
        ).load(request.json)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Patch organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        AdminUnitRelation,
        admin_unit_id_path="source_admin_unit_id",
    )
    def patch(self, id):
        cmd = OrganizationRelationPatchRequestPlainSchema(
            context=g.api_command_context
        ).load(request.json)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Delete organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        AdminUnitRelation,
        admin_unit_id_path="source_admin_unit_id",
    )
    def delete(self, id):
        cmd = DeleteOrganizationRelationCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    OrganizationRelationResource,
    "/organization-relation/<int:id>",
    "api_v1_organization_relation",
)
