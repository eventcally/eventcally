from marshmallow import fields
from marshmallow_enum import EnumField

from project.api.organization.schemas import (
    OrganizationRefSchema,
    OrganizationWriteIdSchema,
)
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
from project.models import AdminUnitVerificationRequest
from project.models.admin_unit_verification_request import (
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
