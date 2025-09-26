from marshmallow import fields

from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
from project.models import AppInstallation


class AppInstallationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AppInstallation
        load_instance = True


class AppInstallationIdSchema(AppInstallationModelSchema, IdSchemaMixin):
    pass


class AppInstallationSchema(AppInstallationIdSchema, TrackableSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    permissions = fields.List(fields.Str())


class AppInstallationRefSchema(AppInstallationSchema):
    pass


class AppInstallationDumpSchema(AppInstallationRefSchema):
    pass


class AppInstallationListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    pass


class AppInstallationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(AppInstallationRefSchema),
        metadata={"description": "App installations"},
    )
