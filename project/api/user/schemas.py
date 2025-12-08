from flask_login import current_user
from marshmallow import fields

from project.api.app.schemas import AppInstallationModelSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
)
from project.models import AdminUnitMember
from project.models.app import AppInstallation


class OrganizationMembershipModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AdminUnitMember
        load_instance = True


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
    class Meta:
        model = AppInstallation
        load_instance = True


class UserAppInstallationIdSchema(UserAppInstallationModelSchema, IdSchemaMixin):
    pass


class UserAppInstallationSchema(UserAppInstallationIdSchema):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    membership = fields.Method("get_membership", dump_only=True)

    def get_membership(self, app_installation):
        if not current_user or not current_user.is_authenticated:  # pragma: no cover
            return None

        admin_unit_member = (
            AdminUnitMember.query.filter(
                AdminUnitMember.admin_unit_id == app_installation.admin_unit_id
            )
            .filter(AdminUnitMember.user_id == current_user.id)
            .first()
        )

        if not admin_unit_member:  # pragma: no cover
            return None

        return OrganizationMembershipSchema().dump(admin_unit_member)


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
