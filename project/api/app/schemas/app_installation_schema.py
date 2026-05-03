from marshmallow import fields

from project.api.app.schemas.app_installation_id_schema import AppInstallationIdSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import TrackableSchemaMixin


class AppInstallationSchema(AppInstallationIdSchema, TrackableSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")
    permissions = fields.List(fields.Str())
