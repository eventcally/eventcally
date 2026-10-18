from marshmallow import fields

from project.presentation.api.app.schemas.app_installation_id_schema import (
    AppInstallationIdSchema,
)
from project.presentation.api.organization.schemas import OrganizationRefSchema
from project.presentation.api.schemas import TrackableSchemaMixin


class AppInstallationSchema(AppInstallationIdSchema, TrackableSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    permissions = fields.List(fields.Str())
