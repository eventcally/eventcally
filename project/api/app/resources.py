from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.app.schemas import (
    AppInstallationListRequestSchema,
    AppInstallationListResponseSchema,
    AppInstallationSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AppInstallation
from project.services.search_params import TrackableSearchParams


class AppInstallationListResource(BaseResource):
    @doc(summary="List app installations", tags=["Apps"])
    @use_kwargs(AppInstallationListRequestSchema, location=("query"))
    @marshal_with(AppInstallationListResponseSchema)
    @require_api_access(app_token_required=True)
    def get(self, **kwargs):
        params = TrackableSearchParams()
        params.load_from_request(**kwargs)

        query = AppInstallation.query.filter(
            AppInstallation.oauth2_client_id == current_token.app_id
        )
        query = params.get_trackable_query(query, AppInstallation)
        query = params.get_trackable_order_by(query, AppInstallation)

        return query.paginate()


add_api_resource(
    AppInstallationListResource,
    "/app/installations",
    "api_v1_app_installation_list",
)


class AppInstallationResource(BaseResource):
    @doc(
        summary="Get app installation",
        tags=["Apps"],
    )
    @marshal_with(AppInstallationSchema)
    @require_api_access(app_token_required=True)
    def get(self, id):
        return (
            AppInstallation.query.filter(
                AppInstallation.oauth2_client_id == current_token.app_id
            )
            .filter(AppInstallation.id == id)
            .first_or_404()
        )


add_api_resource(
    AppInstallationResource,
    "/app/installations/<int:id>",
    "api_v1_app_installation",
)
