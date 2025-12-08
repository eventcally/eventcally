from typing import Annotated

from dependency_injector.wiring import Provide
from flask import g, make_response
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import ValidationError

from project import db
from project.api import add_api_resource
from project.api.organization_relation.schemas import OrganizationRelationIdSchema
from project.api.organization_verification_request.schemas import (
    OrganizationVerificationRequestRejectRequestSchema,
    OrganizationVerificationRequestSchema,
    OrganizationVerificationRequestVerifyRequestSchema,
)
from project.api.resources import BaseResource, require_organization_api_access
from project.models import AdminUnitVerificationRequest
from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequestReviewStatus,
)
from project.services.organization_service import OrganizationService
from project.services.organization_verification_request_service import (
    OrganizationVerificationRequestService,
)


class OrganizationVerificationRequestResource(BaseResource):
    @doc(
        summary="Get organization verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(OrganizationVerificationRequestSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:read",
        AdminUnitVerificationRequest,
        admin_unit_id_path="source_admin_unit_id",
    )
    def get(self, id):
        verification_request = g.manage_admin_unit_instance

        return verification_request

    @doc(
        summary="Delete verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:write",
        AdminUnitVerificationRequest,
        admin_unit_id_path="source_admin_unit_id",
    )
    def delete(self, id):
        verification_request = g.manage_admin_unit_instance
        db.session.delete(verification_request)
        db.session.commit()

        return make_response("", 204)


class OrganizationVerificationRequestVerifyResource(BaseResource):
    organization_service: Annotated[
        OrganizationService, Provide["services.organization_service"]
    ]

    @doc(
        summary="Verify organization verification request. Returns relation id.",
        tags=["Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestVerifyRequestSchema, location="json", apply=True
    )
    @marshal_with(OrganizationRelationIdSchema, 201)
    @require_organization_api_access(
        "organization.incoming_organization_verification_requests:write",
        AdminUnitVerificationRequest,
        admin_unit_id_path="target_admin_unit_id",
    )
    def post(self, id, **kwargs):
        verification_request = g.manage_admin_unit_instance

        if (
            verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.verified
        ):
            raise ValidationError("Verification request already verified")

        relation = (
            self.organization_service.verify_incoming_organization_verification_request(
                verification_request,
                kwargs.get("auto_verify_event_reference_requests", None),
            )
        )
        return relation, 201


class OrganizationVerificationRequestRejectResource(BaseResource):
    organization_verification_request_service: Annotated[
        OrganizationVerificationRequestService,
        Provide["services.organization_verification_request_service"],
    ]

    @doc(
        summary="Reject organization verification request",
        tags=["Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestRejectRequestSchema, location="json", apply=False
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_organization_verification_requests:write",
        AdminUnitVerificationRequest,
        admin_unit_id_path="target_admin_unit_id",
    )
    def post(self, id):
        verification_request = g.manage_admin_unit_instance

        if (
            verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.verified
        ):  # pragma: no cover
            raise ValidationError("Verification request already verified")

        verification_request = self.update_instance(
            OrganizationVerificationRequestRejectRequestSchema,
            instance=verification_request,
        )
        verification_request.review_status = (
            AdminUnitVerificationRequestReviewStatus.rejected
        )

        self.organization_verification_request_service.update_object(
            verification_request
        )
        return make_response("", 204)


add_api_resource(
    OrganizationVerificationRequestResource,
    "/organization-verification-request/<int:id>",
    "api_v1_organization_verification_request",
)
add_api_resource(
    OrganizationVerificationRequestVerifyResource,
    "/organization-verification-request/<int:id>/verify",
    "api_v1_organization_verification_request_verify",
)
add_api_resource(
    OrganizationVerificationRequestRejectResource,
    "/organization-verification-request/<int:id>/reject",
    "api_v1_organization_verification_request_reject",
)
