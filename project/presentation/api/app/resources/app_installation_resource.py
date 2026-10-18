from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with

from project.application.queries import GetAppInstallationForAppQuery
from project.presentation.api import add_api_resource
from project.presentation.api.app.schemas import AppInstallationSchema
from project.presentation.api.resources import BaseResource, require_api_access
from project.presentation.shared.query_results import result_or_404


class AppInstallationResource(BaseResource):
    @doc(
        summary="Get app installation",
        tags=["Apps"],
    )
    @marshal_with(AppInstallationSchema)
    @require_api_access(app_token_required=True)
    def get(self, id):
        return result_or_404(
            self.query_bus.handle(
                GetAppInstallationForAppQuery(app_id=current_token.app_id, id=id)
            )
        )


add_api_resource(
    AppInstallationResource,
    "/app/installations/<int:id>",
    "api_v1_app_installation",
)
