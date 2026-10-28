from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import ValidationError

from project.application.commands import WithdrawOrganizationVerificationRequestCommand
from project.application.queries import (
    GetIncomingOrganizationVerificationRequestQuery,
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


def _get_outgoing(resource, request_id):
    return result_or_404(
        resource.query_bus.handle(
            GetOutgoingOrganizationVerificationRequestQuery(id=request_id)
        )
    )


def _get_incoming(resource, request_id):
    return result_or_404(
        resource.query_bus.handle(
            GetIncomingOrganizationVerificationRequestQuery(id=request_id)
        )
    )


def _withdraw(resource, request_id):
    cmd = WithdrawOrganizationVerificationRequestCommand(
        id=request_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _ensure_not_verified(resource, request_id):
    verification_request = result_or_404(
        resource.query_bus.handle(
            GetIncomingOrganizationVerificationRequestReviewQuery(id=request_id)
        )
    )

    if (
        verification_request.review_status
        == OrganizationVerificationRequestReviewStatus.verified
    ):
        raise ValidationError("Verification request already verified")


def _verify(resource, request_id):
    _ensure_not_verified(resource, request_id)

    cmd = resource.load_command(OrganizationVerificationRequestVerifyRequestPlainSchema)
    cmd_result = resource.message_bus.handle_command(cmd)

    return cmd_result, 201


def _reject(resource, request_id):
    _ensure_not_verified(resource, request_id)

    cmd = resource.load_command(OrganizationVerificationRequestRejectRequestPlainSchema)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


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
        return _get_outgoing(self, id)

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
        return _withdraw(self, id)


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
        return _verify(self, id)


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
        return _reject(self, id)


class OrganizationOutgoingOrganizationVerificationRequestResource(BaseResource):
    @doc(
        summary="Get organization verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(OrganizationVerificationRequestSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:read",
        ResourceKind.verification_request_source,
        item_arg="organization_verification_request_id",
    )
    def get(self, id, organization_verification_request_id):
        return _get_outgoing(self, organization_verification_request_id)

    @doc(
        summary="Delete verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:write",
        ResourceKind.verification_request_source,
        item_arg="organization_verification_request_id",
    )
    def delete(self, id, organization_verification_request_id):
        return _withdraw(self, organization_verification_request_id)


class OrganizationIncomingOrganizationVerificationRequestResource(BaseResource):
    @doc(
        summary="Get incoming organization verification request",
        tags=["Organization Verification Requests"],
    )
    @marshal_with(OrganizationVerificationRequestSchema)
    @require_organization_api_access(
        "organization.incoming_organization_verification_requests:read",
        ResourceKind.verification_request_target,
        item_arg="organization_verification_request_id",
    )
    def get(self, id, organization_verification_request_id):
        return _get_incoming(self, organization_verification_request_id)


class OrganizationIncomingOrganizationVerificationRequestVerifyResource(BaseResource):
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
        item_arg="organization_verification_request_id",
    )
    def post(self, id, organization_verification_request_id):
        return _verify(self, organization_verification_request_id)


class OrganizationIncomingOrganizationVerificationRequestRejectResource(BaseResource):
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
        item_arg="organization_verification_request_id",
    )
    def post(self, id, organization_verification_request_id):
        return _reject(self, organization_verification_request_id)


_OUTGOING_ITEM = (
    "/organizations/<int:id>/outgoing-organization-verification-requests"
    "/<int:organization_verification_request_id>"
)
_INCOMING_ITEM = (
    "/organizations/<int:id>/incoming-organization-verification-requests"
    "/<int:organization_verification_request_id>"
)

add_api_resource(
    OrganizationVerificationRequestResource,
    "/organization-verification-request/<int:id>",
    "api_v1_organization_verification_request",
    deprecated="/organizations/{id}/outgoing-organization-verification-requests/{organization_verification_request_id}",
)
add_api_resource(
    OrganizationVerificationRequestVerifyResource,
    "/organization-verification-request/<int:id>/verify",
    "api_v1_organization_verification_request_verify",
    deprecated="/organizations/{id}/incoming-organization-verification-requests/{organization_verification_request_id}/verify",
)
add_api_resource(
    OrganizationVerificationRequestRejectResource,
    "/organization-verification-request/<int:id>/reject",
    "api_v1_organization_verification_request_reject",
    deprecated="/organizations/{id}/incoming-organization-verification-requests/{organization_verification_request_id}/reject",
)
add_api_resource(
    OrganizationOutgoingOrganizationVerificationRequestResource,
    _OUTGOING_ITEM,
    "api_v1_organization_outgoing_organization_verification_request",
)
add_api_resource(
    OrganizationIncomingOrganizationVerificationRequestResource,
    _INCOMING_ITEM,
    "api_v1_organization_incoming_organization_verification_request",
)
add_api_resource(
    OrganizationIncomingOrganizationVerificationRequestVerifyResource,
    _INCOMING_ITEM + "/verify",
    "api_v1_organization_incoming_organization_verification_request_verify",
)
add_api_resource(
    OrganizationIncomingOrganizationVerificationRequestRejectResource,
    _INCOMING_ITEM + "/reject",
    "api_v1_organization_incoming_organization_verification_request_reject",
)
