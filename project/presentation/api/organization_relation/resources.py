from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project.application.commands import DeleteOrganizationRelationCommand
from project.application.queries import (
    GetOutgoingOrganizationRelationQuery,
    ResourceKind,
)
from project.presentation.api import add_api_resource
from project.presentation.api.organization_relation.schemas import (
    OrganizationRelationPatchRequestPlainSchema,
    OrganizationRelationPatchRequestSchema,
    OrganizationRelationPutRequestPlainSchema,
    OrganizationRelationSchema,
    OrganizationRelationUpdateRequestSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


class OrganizationRelationResource(BaseResource):
    @doc(
        summary="Get organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:read",
        ResourceKind.organization_relation,
    )
    def get(self, id):
        return result_or_404(
            self.query_bus.handle(GetOutgoingOrganizationRelationQuery(id=id))
        )

    @doc(
        summary="Update organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        ResourceKind.organization_relation,
    )
    def put(self, id):
        cmd = self.load_command(OrganizationRelationPutRequestPlainSchema)
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
        ResourceKind.organization_relation,
    )
    def patch(self, id):
        cmd = self.load_command(OrganizationRelationPatchRequestPlainSchema)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Delete organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        ResourceKind.organization_relation,
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
