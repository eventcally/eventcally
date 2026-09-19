from marshmallow import fields, post_load
from marshmallow_enum import EnumField

from project.api.organization.schemas import (
    OrganizationRefSchema,
    OrganizationWriteIdPlainSchema,
    OrganizationWriteIdSchema,
)
from project.api.schemas import (
    IdPlainSchemaMixin,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
from project.application.commands import (
    ApproveOrganizationVerificationRequestCommand,
    RejectOrganizationVerificationRequestCommand,
    RequestOrganizationVerificationCommand,
)
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.models import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestRejectionReason,
    AdminUnitVerificationRequestReviewStatus,
)


class OrganizationVerificationRequestModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AdminUnitVerificationRequest
        load_instance = True


class OrganizationVerificationRequestIdSchema(
    OrganizationVerificationRequestModelSchema, IdSchemaMixin
):
    pass


class OrganizationVerificationRequestBaseSchemaMixin(TrackableSchemaMixin):
    review_status = EnumField(
        AdminUnitVerificationRequestReviewStatus,
        load_default=AdminUnitVerificationRequestReviewStatus.inbox,
    )
    rejection_reason = EnumField(
        AdminUnitVerificationRequestRejectionReason,
    )


class OrganizationVerificationRequestRefSchema(
    OrganizationVerificationRequestIdSchema, TrackableSchemaMixin
):
    source_organization = fields.Nested(
        OrganizationRefSchema, attribute="source_admin_unit"
    )
    target_organization = fields.Nested(
        OrganizationRefSchema, attribute="target_admin_unit"
    )


class OrganizationVerificationRequestSchema(
    OrganizationVerificationRequestIdSchema,
    OrganizationVerificationRequestBaseSchemaMixin,
):
    source_organization = fields.Nested(
        OrganizationRefSchema, attribute="source_admin_unit"
    )
    target_organization = fields.Nested(
        OrganizationRefSchema, attribute="target_admin_unit"
    )


class OrganizationVerificationRequestListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    pass


class OrganizationVerificationRequestListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizationVerificationRequestRefSchema),
        metadata={"description": "Organization verification requests"},
    )


class OrganizationVerificationRequestWriteSchemaMixin(object):
    target_organization = fields.Nested(
        OrganizationWriteIdSchema,
        attribute="target_admin_unit",
        required=True,
        metadata={"description": "Target organization."},
    )


class OrganizationVerificationRequestPostRequestSchema(
    OrganizationVerificationRequestModelSchema,
    OrganizationVerificationRequestWriteSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class OrganizationVerificationRequestVerifyRequestSchema(SQLAlchemyBaseSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    auto_verify_event_reference_requests = fields.Bool()


class OrganizationVerificationRequestRejectRequestSchema(
    OrganizationVerificationRequestModelSchema,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    rejection_reason = EnumField(
        AdminUnitVerificationRequestRejectionReason,
    )


class OrganizationVerificationRequestIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class OrganizationVerificationRequestCreateRequestPlainSchema(PlainBaseSchema):
    target_organization = fields.Nested(
        OrganizationWriteIdPlainSchema,
        attribute="target_admin_unit_id",
        required=True,
        metadata={"description": "Target organization."},
    )

    @post_load
    def make_instance(self, data, **kwargs):
        data["source_admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return RequestOrganizationVerificationCommand(**data)


class OrganizationVerificationRequestVerifyRequestPlainSchema(PlainBaseSchema):
    auto_verify_event_reference_requests = fields.Bool(
        allow_none=True, load_default=None
    )

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return ApproveOrganizationVerificationRequestCommand(**data)


class OrganizationVerificationRequestRejectRequestPlainSchema(PlainBaseSchema):
    rejection_reason = EnumField(
        OrganizationVerificationRequestRejectionReason,
        allow_none=True,
        load_default=None,
    )

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return RejectOrganizationVerificationRequestCommand(**data)
