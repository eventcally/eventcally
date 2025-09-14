from marshmallow import fields

from project.api import marshmallow
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
)
from project.models import AppInstallation


class AppInstallationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AppInstallation
        load_instance = True


class AppInstallationIdSchema(AppInstallationModelSchema, IdSchemaMixin):
    pass


class AppInstallationRefSchema(AppInstallationIdSchema):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    permissions = marshmallow.auto_field()


class AppInstallationDumpSchema(AppInstallationRefSchema):
    pass


class AppInstallationListRequestSchema(PaginationRequestSchema):
    pass


class AppInstallationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(AppInstallationRefSchema),
        metadata={"description": "App installations"},
    )
