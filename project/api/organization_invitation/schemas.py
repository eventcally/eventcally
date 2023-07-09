from marshmallow import fields, validate

from project.api import marshmallow
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
from project.models import AdminUnitInvitation


class OrganizationInvitationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AdminUnitInvitation
        load_instance = True


class OrganizationInvitationIdSchema(OrganizationInvitationModelSchema, IdSchemaMixin):
    pass


class OrganizationInvitationBaseSchemaMixin(TrackableSchemaMixin):
    organization_name = fields.Str(attribute="admin_unit_name")
    relation_auto_verify_event_reference_requests = marshmallow.auto_field()
    relation_verify = marshmallow.auto_field()


class OrganizationInvitationSchema(
    OrganizationInvitationIdSchema, OrganizationInvitationBaseSchemaMixin
):
    email = marshmallow.auto_field()
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class OrganizationInvitationRefSchema(OrganizationInvitationIdSchema):
    organization_name = fields.Str(attribute="admin_unit_name")
    email = marshmallow.auto_field()


class OrganizationInvitationListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            ["-created_at", "-updated_at", "-last_modified_at", "name"]
        ),
    )


class OrganizationInvitationListRefSchema(
    OrganizationInvitationRefSchema, TrackableSchemaMixin
):
    pass


class OrganizationInvitationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizationInvitationListRefSchema),
        metadata={"description": "Organization invitations"},
    )


class OrganizationInvitationWriteSchemaMixin(object):
    email = marshmallow.auto_field()


class OrganizationInvitationCreateRequestSchema(
    OrganizationInvitationModelSchema,
    OrganizationInvitationBaseSchemaMixin,
    OrganizationInvitationWriteSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class OrganizationInvitationUpdateRequestSchema(
    OrganizationInvitationModelSchema,
    OrganizationInvitationBaseSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class OrganizationInvitationPatchRequestSchema(
    OrganizationInvitationModelSchema,
    OrganizationInvitationBaseSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()
