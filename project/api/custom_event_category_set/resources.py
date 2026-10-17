from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.custom_event_category_set.schemas import (
    CustomEventCategorySetListRequestSchema,
    CustomEventCategorySetListResponseSchema,
)
from project.api.query_args import page_request_from_kwargs
from project.api.resources import BaseResource, require_api_access
from project.application.queries import (
    ListCustomEventCategoriesQuery,
    ListCustomEventCategorySetsQuery,
)
from project.views.utils import abort_if_page_out_of_range


class CustomEventCategorySetListResource(BaseResource):
    @doc(summary="List custom event category sets", tags=["Event Categories"])
    @use_kwargs(CustomEventCategorySetListRequestSchema, location=("query"))
    @marshal_with(CustomEventCategorySetListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListCustomEventCategorySetsQuery(page=page_request_from_kwargs(kwargs))
        )
        abort_if_page_out_of_range(page)
        return page


class CustomEventCategorySetEventCategoryListResource(BaseResource):
    @doc(summary="List custom event categories", tags=["Event Categories"])
    @use_kwargs(CustomEventCategorySetListRequestSchema, location=("query"))
    @marshal_with(CustomEventCategorySetListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        page = self.query_bus.handle(
            ListCustomEventCategoriesQuery(
                category_set_id=id, page=page_request_from_kwargs(kwargs)
            )
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(
    CustomEventCategorySetListResource,
    "/custom-event-category-sets",
    "api_v1_custom_event_category_set_list",
)

add_api_resource(
    CustomEventCategorySetEventCategoryListResource,
    "/custom-event-category-set/<int:id>/custom-event-categories",
    "api_v1_custom_event_category_set_event_category_list",
)
