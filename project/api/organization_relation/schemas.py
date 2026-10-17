from marshmallow import fields, post_load

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
    TrackableSchemaMixin,
)
from project.application.commands import (
    CreateOrganizationRelationCommand,
    UpdateOrganizationRelationCommand,
)


class OrganizationRelationModelSchema(PlainBaseSchema):
    pass


class OrganizationRelationIdSchema(OrganizationRelationModelSchema, IdSchemaMixin):
    pass


class OrganizationRelationBaseSchemaMixin(TrackableSchemaMixin):
    auto_verify_event_reference_requests = fields.Boolean()
    verify = fields.Boolean()


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


class OrganizationRelationIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class OrganizationRelationCreateRequestPlainSchema(PlainBaseSchema):
    target_organization = fields.Nested(
        OrganizationWriteIdPlainSchema,
        attribute="target_admin_unit_id",
        required=True,
        metadata={"description": "Target organization."},
    )
    auto_verify_event_reference_requests = fields.Bool(load_default=False)
    verify = fields.Bool(load_default=False)

    @post_load
    def make_instance(self, data, **kwargs):
        data["source_admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return CreateOrganizationRelationCommand(**data)


class OrganizationRelationPutRequestPlainSchema(PlainBaseSchema):
    auto_verify_event_reference_requests = fields.Bool(load_default=False)
    verify = fields.Bool(load_default=False)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateOrganizationRelationCommand(**data)


class OrganizationRelationPatchRequestPlainSchema(PlainBaseSchema):
    auto_verify_event_reference_requests = fields.Bool(allow_none=True)
    verify = fields.Bool(allow_none=True)

    @post_load
    def make_instance(self, data, **kwargs):
        data = {key: value for key, value in data.items() if value is not None}
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateOrganizationRelationCommand(**data)
