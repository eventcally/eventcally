from typing import Optional

from flask import current_app, request

from project.application.queries import (
    GetCustomEventCategoryQuery,
    GetEventCategoryQuery,
    GetLicenseQuery,
    ListAllEventCategoriesQuery,
    LookupCustomEventCategoriesQuery,
    LookupLicensesQuery,
    PageRequest,
)
from project.application.queries.base import Query
from project.application.query_bus import QueryBus
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    page_request_from_request_args,
)
from project.shared.utils import get_event_category_name


class QueryAjaxLoader:
    """Select2 loader backed by queries.

    Subclasses build the lookup and get queries; both answer read models that expose
    at least `id`. `format_model` may also receive ORM objects (forms still filled from
    the ORM), so it only reads attributes both have.
    """

    def __init__(self, **kwargs):
        self.placeholder = kwargs.pop("placeholder", None)
        self.minimum_input_length = int(kwargs.pop("minimum_input_length", 0))
        self.options = kwargs

    @property
    def query_bus(self) -> QueryBus:
        return current_app.container.cqrs.query_bus()

    def get_lookup_query(
        self, term: Optional[str], page_request: PageRequest
    ) -> Query:  # pragma: no cover
        raise NotImplementedError

    def get_one_query(self, pk: int) -> Query:  # pragma: no cover
        raise NotImplementedError

    def format(self, model):
        if not model:  # pragma: no cover
            return None

        return model.id, self.format_model(model)

    def format_model(self, model):
        return model.name

    def get_one(self, pk):
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return None

        return self.query_bus.handle(self.get_one_query(pk))

    def get_pagination(self, term):
        page_request = page_request_from_request_args()
        page = self.query_bus.handle(self.get_lookup_query(term, page_request))
        abort_if_page_out_of_range(page)
        return page

    def get_ajax_pagination(self, term):
        pagination = self.get_pagination(term)
        return {
            "items": [self.format(m) for m in pagination.items],
            "has_next": pagination.has_next,
        }


class EventCategoryAjaxModelLoader(QueryAjaxLoader):
    def get_one_query(self, pk):
        return GetEventCategoryQuery(id=pk)

    def get_ajax_pagination(self, term):
        categories = self.query_bus.handle(ListAllEventCategoriesQuery())
        all = sorted(
            [(c.id, self.format_model(c)) for c in categories],
            key=lambda category: category[1],
        )
        matching = [i for i in all if term in i[1]] if term else all

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        start = (page - 1) * per_page
        end = start + per_page
        sliced = matching[start:end]

        return {
            "items": sliced,
            "has_next": len(matching) > len(sliced),
        }

    def format_model(self, model):
        return get_event_category_name(model)


class CustomEventCategoryLoader(QueryAjaxLoader):
    def __init__(self, **kwargs):
        self.category_set_id = kwargs.pop("category_set_id")
        super().__init__(**kwargs)

    def get_lookup_query(self, term, page_request):
        return LookupCustomEventCategoriesQuery(
            category_set_id=self.category_set_id, term=term, page=page_request
        )

    def get_one_query(self, pk):
        return GetCustomEventCategoryQuery(id=pk)

    def format_model(self, model):
        return model.label_or_name


class LicenseAjaxModelLoader(QueryAjaxLoader):
    def get_lookup_query(self, term, page_request):
        return LookupLicensesQuery(term=term, page=page_request)

    def get_one_query(self, pk):
        return GetLicenseQuery(id=pk)

    def format_model(self, model):
        return f"{model.code} ({model.name})"
