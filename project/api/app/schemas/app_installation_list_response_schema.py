from marshmallow import fields

from project.api.app.schemas.app_installation_ref_schema import AppInstallationRefSchema
from project.api.schemas import PaginationResponseSchema


class AppInstallationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(AppInstallationRefSchema),
        metadata={"description": "App installations"},
    )
