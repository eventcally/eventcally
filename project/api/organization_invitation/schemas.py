from marshmallow import fields, post_load, validate

from project.api import marshmallow
from project.api.organization.schemas import OrganizationRefSchema
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
    InviteOrganizationCommand,
    UpdateOrganizationInvitationCommand,
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
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


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


class OrganizationInvitationIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class OrganizationInvitationCreateRequestPlainSchema(PlainBaseSchema):
    email = fields.Email(required=True)
    organization_name = fields.Str(attribute="admin_unit_name", load_default=None)
    relation_auto_verify_event_reference_requests = fields.Bool(load_default=False)
    relation_verify = fields.Bool(load_default=False)

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return InviteOrganizationCommand(**data)


class OrganizationInvitationPutRequestPlainSchema(PlainBaseSchema):
    organization_name = fields.Str(attribute="admin_unit_name", load_default=None)
    relation_auto_verify_event_reference_requests = fields.Bool(load_default=False)
    relation_verify = fields.Bool(load_default=False)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateOrganizationInvitationCommand(**data)


class OrganizationInvitationPatchRequestPlainSchema(PlainBaseSchema):
    organization_name = fields.Str(attribute="admin_unit_name", allow_none=True)
    relation_auto_verify_event_reference_requests = fields.Bool(allow_none=True)
    relation_verify = fields.Bool(allow_none=True)

    @post_load
    def make_instance(self, data, **kwargs):
        for key in (
            "relation_auto_verify_event_reference_requests",
            "relation_verify",
        ):
            if data.get(key) is None:
                data.pop(key, None)
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateOrganizationInvitationCommand(**data)
