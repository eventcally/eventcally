from marshmallow import fields

from project.presentation.api.app.schemas import AppInstallationModelSchema
from project.presentation.api.organization.schemas import OrganizationRefSchema
from project.presentation.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
)


class OrganizationMembershipModelSchema(PlainBaseSchema):
    pass


class OrganizationMembershipIdSchema(OrganizationMembershipModelSchema, IdSchemaMixin):
    pass


class OrganizationMembershipSchema(OrganizationMembershipIdSchema):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    is_admin = fields.Bool(dump_only=True)


class OrganizationMembershipRefSchema(OrganizationMembershipSchema):
    pass


class OrganizationMembershipListRequestSchema(PaginationRequestSchema):
    pass


class OrganizationMembershipListRefSchema(OrganizationMembershipRefSchema):
    pass


class OrganizationMembershipListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizationMembershipListRefSchema),
        metadata={"description": "Organization memberships"},
    )


class UserAppInstallationModelSchema(AppInstallationModelSchema):
    pass


class UserAppInstallationIdSchema(UserAppInstallationModelSchema, IdSchemaMixin):
    pass


class UserAppInstallationSchema(UserAppInstallationIdSchema):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    membership = fields.Method("get_membership", dump_only=True)

    def get_membership(self, app_installation):
        if app_installation.membership is None:  # pragma: no cover
            return None

        return OrganizationMembershipSchema().dump(app_installation.membership)


class UserAppInstallationRefSchema(UserAppInstallationSchema):
    pass


class UserAppInstallationListRequestSchema(PaginationRequestSchema):
    admin_only = fields.Bool(
        metadata={"description": "Include only installation where user is admin"},
    )


class UserAppInstallationListRefSchema(UserAppInstallationRefSchema):
    pass


class UserAppInstallationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(UserAppInstallationListRefSchema),
        metadata={"description": "App installations"},
    )
