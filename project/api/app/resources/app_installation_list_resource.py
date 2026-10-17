from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.app.schemas import (
    AppInstallationListRequestSchema,
    AppInstallationListResponseSchema,
)
from project.api.query_args import (
    page_request_from_kwargs,
    trackable_criteria_from_kwargs,
    trackable_sort_from_kwargs,
)
from project.api.resources import BaseResource, require_api_access
from project.application.queries import ListAppInstallationsForAppQuery
from project.views.utils import abort_if_page_out_of_range


class AppInstallationListResource(BaseResource):
    @doc(summary="List app installations", tags=["Apps"])
    @use_kwargs(AppInstallationListRequestSchema, location=("query"))
    @marshal_with(AppInstallationListResponseSchema)
    @require_api_access(app_token_required=True)
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListAppInstallationsForAppQuery(
                app_id=current_token.app_id,
                trackable=trackable_criteria_from_kwargs(kwargs),
                sort=trackable_sort_from_kwargs(kwargs),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(
    AppInstallationListResource,
    "/app/installations",
    "api_v1_app_installation_list",
)
