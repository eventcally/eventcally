from flask import abort
from flask.helpers import make_response
from flask_apispec import doc, marshal_with
from flask_apispec.annotations import use_kwargs

from project import db
from project.access import access_or_401, has_access, login_api_user_or_401
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
        security=[{"oauth2": ["organization:read"]}],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_api_access("organization:read")
    def get(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)

        if not has_access(
            relation.source_admin_unit, "admin_unit:update"
        ) and not has_access(relation.target_admin_unit, "admin_unit:update"):
            abort(401)

        return relation

    @doc(
        summary="Update organization relation",
        tags=["Organization Relations"],
        security=[{"oauth2": ["organization:write"]}],
    )
    @use_kwargs(OrganizationRelationUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("organization:write")
    def put(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(relation.source_admin_unit, "admin_unit:update")

        relation = self.update_instance(
            OrganizationRelationUpdateRequestSchema, instance=relation
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch organization relation",
        tags=["Organization Relations"],
        security=[{"oauth2": ["organization:write"]}],
    )
    @use_kwargs(OrganizationRelationPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("organization:write")
    def patch(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(relation.source_admin_unit, "admin_unit:update")

        relation = self.update_instance(
            OrganizationRelationPatchRequestSchema, instance=relation
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete organization relation",
        tags=["Organization Relations"],
        security=[{"oauth2": ["organization:write"]}],
    )
    @marshal_with(None, 204)
    @require_api_access("organization:write")
    def delete(self, id):
        login_api_user_or_401()
        relation = AdminUnitRelation.query.get_or_404(id)
        access_or_401(relation.source_admin_unit, "admin_unit:update")

        db.session.delete(relation)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    OrganizationRelationResource,
    "/organization-relation/<int:id>",
    "api_v1_organization_relation",
)
