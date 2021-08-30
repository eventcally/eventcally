from marshmallow import fields

from project.api import marshmallow
from project.api.organization.schemas import (
    OrganizationRefSchema,
    OrganizationWriteIdSchema,
)
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableSchemaMixin,
)
from project.models import AdminUnitRelation


class OrganizationRelationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AdminUnitRelation
        load_instance = True


class OrganizationRelationIdSchema(OrganizationRelationModelSchema, IdSchemaMixin):
    pass


class OrganizationRelationBaseSchemaMixin(TrackableSchemaMixin):
    auto_verify_event_reference_requests = marshmallow.auto_field()


class OrganizationRelationSchema(
    OrganizationRelationIdSchema, OrganizationRelationBaseSchemaMixin
):
    source_organization = fields.Nested(
        OrganizationRefSchema, attribute="source_admin_unit"
    )
    target_organization = fields.Nested(
        OrganizationRefSchema, attribute="target_admin_unit"
    )


class OrganizationRelationRefSchema(OrganizationRelationIdSchema):
    source_organization = fields.Nested(
        OrganizationRefSchema, attribute="source_admin_unit"
    )
    target_organization = fields.Nested(
        OrganizationRefSchema, attribute="target_admin_unit"
    )


class OrganizationRelationListRequestSchema(PaginationRequestSchema):
    pass


class OrganizationRelationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizationRelationRefSchema),
        metadata={"description": "Organization relations"},
    )


class OrganizationRelationWriteSchemaMixin(object):
    target_organization = fields.Nested(
        OrganizationWriteIdSchema,
        attribute="target_admin_unit",
        required=True,
        metadata={"description": "Target organization."},
    )


class OrganizationRelationCreateRequestSchema(
    OrganizationRelationModelSchema,
    OrganizationRelationBaseSchemaMixin,
    OrganizationRelationWriteSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class OrganizationRelationUpdateRequestSchema(
    OrganizationRelationModelSchema,
    OrganizationRelationBaseSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class OrganizationRelationPatchRequestSchema(
    OrganizationRelationModelSchema,
    OrganizationRelationBaseSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()
