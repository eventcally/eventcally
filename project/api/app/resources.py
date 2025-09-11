from authlib.integrations.flask_oauth2 import current_token
from flask import abort
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.app.schemas import (
    AppInstallationListRequestSchema,
    AppInstallationListResponseSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AppInstallation, OAuth2Client


class AppInstallationListResource(BaseResource):
    @doc(summary="List app installations", tags=["Apps"])
    @use_kwargs(AppInstallationListRequestSchema, location=("query"))
    @marshal_with(AppInstallationListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        if not current_token or not current_token.app_id:  # pragma: no cover
            abort(401)

        app = OAuth2Client.query.get_or_404(current_token.app_id)
        pagination = AppInstallation.query.filter(
            AppInstallation.oauth2_client_id == app.id
        ).paginate()
        return pagination


add_api_resource(
    AppInstallationListResource,
    "/app/installations",
    "api_v1_app_installation_list",
)
