from flask_apispec import doc, marshal_with, use_kwargs

from project.application.queries import ListLicensesQuery
from project.presentation.api import add_api_resource
from project.presentation.api.license.schemas import (
    LicenseListRequestSchema,
    LicenseListResponseSchema,
)
from project.presentation.api.resources import BaseResource, require_api_access
from project.presentation.shared.query_args import page_request_from_kwargs
from project.presentation.shared.query_results import abort_if_page_out_of_range


class LicenseListResource(BaseResource):
    @doc(summary="List licenses", tags=["Licenses"])
    @use_kwargs(LicenseListRequestSchema, location=("query"))
    @marshal_with(LicenseListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListLicensesQuery(page=page_request_from_kwargs(kwargs))
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(LicenseListResource, "/licenses", "api_v1_license_list")
