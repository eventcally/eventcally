from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import ValidationError

from project.application.commands import WithdrawOrganizationVerificationRequestCommand
from project.application.queries import (
    GetIncomingOrganizationVerificationRequestReviewQuery,
    GetOutgoingOrganizationVerificationRequestQuery,
    ResourceKind,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.presentation.api import add_api_resource
from project.presentation.api.organization_relation.schemas import (
    OrganizationRelationIdPlainSchema,
)
from project.presentation.api.organization_verification_request.schemas import (
    OrganizationVerificationRequestRejectRequestPlainSchema,
    OrganizationVerificationRequestRejectRequestSchema,
    OrganizationVerificationRequestSchema,
    OrganizationVerificationRequestVerifyRequestPlainSchema,
    OrganizationVerificationRequestVerifyRequestSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


class OrganizationVerificationRequestResource(BaseResource):
    @doc(
        summary="Get organization verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(OrganizationVerificationRequestSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:read",
        ResourceKind.verification_request_source,
    )
    def get(self, id):
        return result_or_404(
            self.query_bus.handle(
                GetOutgoingOrganizationVerificationRequestQuery(id=id)
            )
        )

    @doc(
        summary="Delete verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:write",
        ResourceKind.verification_request_source,
    )
    def delete(self, id):
        cmd = WithdrawOrganizationVerificationRequestCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


class OrganizationVerificationRequestVerifyResource(BaseResource):
    @doc(
        summary="Verify organization verification request. Returns relation id.",
        tags=["Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestVerifyRequestSchema, location="json", apply=False
    )
    @marshal_with(OrganizationRelationIdPlainSchema, 201)
    @require_organization_api_access(
        "organization.incoming_organization_verification_requests:write",
        ResourceKind.verification_request_target,
    )
    def post(self, id, **kwargs):
        verification_request = result_or_404(
            self.query_bus.handle(
                GetIncomingOrganizationVerificationRequestReviewQuery(id=id)
            )
        )

        if (
            verification_request.review_status
            == OrganizationVerificationRequestReviewStatus.verified
        ):
            raise ValidationError("Verification request already verified")

        cmd = self.load_command(OrganizationVerificationRequestVerifyRequestPlainSchema)
        cmd_result = self.message_bus.handle_command(cmd)

        return cmd_result, 201


class OrganizationVerificationRequestRejectResource(BaseResource):
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
        ResourceKind.verification_request_target,
    )
    def post(self, id):
        verification_request = result_or_404(
            self.query_bus.handle(
                GetIncomingOrganizationVerificationRequestReviewQuery(id=id)
            )
        )

        if (
            verification_request.review_status
            == OrganizationVerificationRequestReviewStatus.verified
        ):  # pragma: no cover
            raise ValidationError("Verification request already verified")

        cmd = self.load_command(OrganizationVerificationRequestRejectRequestPlainSchema)
        self.message_bus.handle_command(cmd)

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
