from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project import db
from project.access import access_or_401, login_api_user_or_401
from project.api import add_api_resource
from project.api.organization_relation.schemas import (
    OrganizationRelationPatchRequestSchema,
    OrganizationRelationSchema,
    OrganizationRelationUpdateRequestSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AdminUnitRelation


class OrganizationRelationResource(BaseResource):
    @doc(
        summary="Get organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_api_access("organization.outgoing_organization_relations:read")
    def get(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(
            relation.source_admin_unit, "outgoing_organization_relations:read"
        )

        return relation

    @doc(
        summary="Update organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("organization.outgoing_organization_relations:write")
    def put(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(
            relation.source_admin_unit, "outgoing_organization_relations:write"
        )

        relation = self.update_instance(
            OrganizationRelationUpdateRequestSchema, instance=relation
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch organization relation",
        tags=["Organization Relations"],
    )
    @use_kwargs(OrganizationRelationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("organization.outgoing_organization_relations:write")
    def patch(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(
            relation.source_admin_unit, "outgoing_organization_relations:write"
        )

        relation = self.update_instance(
            OrganizationRelationPatchRequestSchema, instance=relation
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete organization relation",
        tags=["Organization Relations"],
    )
    @marshal_with(None, 204)
    @require_api_access("organization.outgoing_organization_relations:write")
    def delete(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(
            relation.source_admin_unit, "outgoing_organization_relations:write"
        )

        db.session.delete(relation)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    OrganizationRelationResource,
    "/organization-relation/<int:id>",
    "api_v1_organization_relation",
)
