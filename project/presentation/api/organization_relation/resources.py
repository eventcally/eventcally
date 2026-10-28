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


def _get(resource, relation_id):
    return result_or_404(
        resource.query_bus.handle(GetOutgoingOrganizationRelationQuery(id=relation_id))
    )


def _put(resource):
    cmd = resource.load_command(OrganizationRelationPutRequestPlainSchema)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _patch(resource):
    cmd = resource.load_command(OrganizationRelationPatchRequestPlainSchema)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _delete(resource, relation_id):
    cmd = DeleteOrganizationRelationCommand(
        id=relation_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


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
        return _get(self, id)

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
        return _put(self)

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
        return _patch(self)

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
        return _delete(self, id)


class OrganizationOutgoingOrganizationRelationResource(BaseResource):
    @doc(
        summary="Get outgoing organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:read",
        ResourceKind.organization_relation,
        item_arg="organization_relation_id",
    )
    def get(self, id, organization_relation_id):
        return _get(self, organization_relation_id)

    @doc(
        summary="Update organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        ResourceKind.organization_relation,
        item_arg="organization_relation_id",
    )
    def put(self, id, organization_relation_id):
        return _put(self)

    @doc(
        summary="Patch organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        ResourceKind.organization_relation,
        item_arg="organization_relation_id",
    )
    def patch(self, id, organization_relation_id):
        return _patch(self)

    @doc(
        summary="Delete organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write",
        ResourceKind.organization_relation,
        item_arg="organization_relation_id",
    )
    def delete(self, id, organization_relation_id):
        return _delete(self, organization_relation_id)


add_api_resource(
    OrganizationRelationResource,
    "/organization-relation/<int:id>",
    "api_v1_organization_relation",
    deprecated="/organizations/{id}/outgoing-organization-relations/{organization_relation_id}",
)
add_api_resource(
    OrganizationOutgoingOrganizationRelationResource,
    "/organizations/<int:id>/outgoing-organization-relations/<int:organization_relation_id>",
    "api_v1_organization_outgoing_organization_relation",
)
