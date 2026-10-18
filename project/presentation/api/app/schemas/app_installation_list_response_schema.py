from marshmallow import fields

from project.presentation.api.app.schemas.app_installation_ref_schema import (
    AppInstallationRefSchema,
)
from project.presentation.api.schemas import PaginationResponseSchema


class AppInstallationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(AppInstallationRefSchema),
        metadata={"description": "App installations"},
    )
