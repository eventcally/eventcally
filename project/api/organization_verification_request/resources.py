from flask import abort, make_response
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import ValidationError

from project import db
from project.access import access_or_401, has_access, login_api_user_or_401
from project.api import add_api_resource
from project.api.organization_relation.schemas import OrganizationRelationIdSchema
from project.api.organization_verification_request.schemas import (
    OrganizationVerificationRequestRejectRequestSchema,
    OrganizationVerificationRequestSchema,
    OrganizationVerificationRequestVerifyRequestSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AdminUnitVerificationRequest
from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequestReviewStatus,
)
from project.services.admin_unit import upsert_admin_unit_relation
from project.views.verification_request_review import (
    send_verification_request_review_status_mails,
)


class OrganizationVerificationRequestResource(BaseResource):
    @doc(
        summary="Get organization verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(OrganizationVerificationRequestSchema)
    @require_api_access("organizationverificationrequest:read")
    def get(self, id):
        login_api_user_or_401()
        verification_request = AdminUnitVerificationRequest.query.get_or_404(id)

        if not has_access(
            verification_request.source_admin_unit, "verification_request:read"
        ) and not has_access(
            verification_request.target_admin_unit, "verification_request:verify"
        ):
            abort(401)

        return verification_request

    @doc(
        summary="Delete verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(None, 204)
    @require_api_access("organizationverificationrequest:write")
    def delete(self, id):
        login_api_user_or_401()
        verification_request = AdminUnitVerificationRequest.query.get_or_404(id)
        access_or_401(
            verification_request.source_admin_unit, "verification_request:delete"
        )

        db.session.delete(verification_request)
        db.session.commit()

        return make_response("", 204)


class OrganizationVerificationRequestVerifyResource(BaseResource):
    @doc(
        summary="Verify organization verification request. Returns relation id.",
        tags=["Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestVerifyRequestSchema, location="json", apply=True
    )
    @marshal_with(OrganizationRelationIdSchema, 201)
    @require_api_access("organizationverificationrequest:write")
    def post(self, id, **kwargs):
        login_api_user_or_401()
        verification_request = AdminUnitVerificationRequest.query.get_or_404(id)
        access_or_401(
            verification_request.target_admin_unit, "verification_request:verify"
        )

        if (
            verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.verified
        ):
            raise ValidationError("Verification request already verified")

        verification_request.review_status = (
            AdminUnitVerificationRequestReviewStatus.verified
        )

        relation = upsert_admin_unit_relation(
            verification_request.target_admin_unit_id,
            verification_request.source_admin_unit_id,
        )
        relation.verify = True
        relation.auto_verify_event_reference_requests = kwargs.get(
            "auto_verify_event_reference_requests",
            relation.auto_verify_event_reference_requests,
        )
        db.session.commit()

        send_verification_request_review_status_mails(verification_request)
        return relation, 201


class OrganizationVerificationRequestRejectResource(BaseResource):
    @doc(
        summary="Reject organization verification request",
        tags=["Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestRejectRequestSchema, location="json", apply=False
    )
    @marshal_with(None, 204)
    @require_api_access("organizationverificationrequest:write")
    def post(self, id):
        login_api_user_or_401()
        verification_request = AdminUnitVerificationRequest.query.get_or_404(id)
        access_or_401(
            verification_request.target_admin_unit, "verification_request:verify"
        )

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
        db.session.commit()

        send_verification_request_review_status_mails(verification_request)
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
