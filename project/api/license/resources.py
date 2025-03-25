from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.license.schemas import (
    LicenseListRequestSchema,
    LicenseListResponseSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import License


class LicenseListResource(BaseResource):
    @doc(summary="List licenses", tags=["Licenses"])
    @use_kwargs(LicenseListRequestSchema, location=("query"))
    @marshal_with(LicenseListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        pagination = License.query.paginate()
        return pagination


add_api_resource(LicenseListResource, "/licenses", "api_v1_license_list")
