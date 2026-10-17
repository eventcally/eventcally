"""Reference data query handlers — public pass-through to the repository."""

from project.application import queries
from project.application.query_handlers import (
    GetCustomEventCategoryHandler,
    GetEventCategoryByNameHandler,
    GetEventCategoryHandler,
    GetLicenseHandler,
    ListAllEventCategoriesHandler,
    ListCustomEventCategoriesHandler,
    ListCustomEventCategorySetsHandler,
    ListEventCategoriesHandler,
    ListLicensesHandler,
    LookupCustomEventCategoriesHandler,
    LookupLicensesHandler,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_reference_data_read_repository import (
    AbstractReferenceDataReadRepository,
)


class FakeRepo(AbstractReferenceDataReadRepository):
    def __init__(self):
        self.calls = []

    def _page(self, name, query):
        self.calls.append((name, query))
        return Page(items=[], page=1, per_page=20, total=0)

    def list_licenses(self, query):
        return self._page("licenses", query)

    def list_event_categories(self, query):
        return self._page("event_categories", query)

    def list_custom_event_category_sets(self, query):
        return self._page("sets", query)

    def list_custom_event_categories(self, query):
        return self._page("categories", query)

    def lookup_licenses(self, query):
        return self._page("lookup_licenses", query)

    def get_license(self, license_id):
        self.calls.append(("get_license", license_id))

    def list_all_event_categories(self):
        self.calls.append(("all_event_categories", None))
        return []

    def get_event_category(self, category_id):
        self.calls.append(("get_event_category", category_id))

    def get_event_category_by_name(self, name):
        self.calls.append(("get_event_category_by_name", name))

    def lookup_custom_event_categories(self, query):
        return self._page("lookup_custom", query)

    def get_custom_event_category(self, category_id):
        self.calls.append(("get_custom_event_category", category_id))


def test_handlers_pass_queries_through():
    repo = FakeRepo()

    ListLicensesHandler(repo).handle(queries.ListLicensesQuery())
    ListEventCategoriesHandler(repo).handle(queries.ListEventCategoriesQuery())
    ListCustomEventCategorySetsHandler(repo).handle(
        queries.ListCustomEventCategorySetsQuery()
    )
    ListCustomEventCategoriesHandler(repo).handle(
        queries.ListCustomEventCategoriesQuery(category_set_id=1)
    )

    assert [name for name, _ in repo.calls] == [
        "licenses",
        "event_categories",
        "sets",
        "categories",
    ]


def test_lookup_handlers_pass_queries_through():
    repo = FakeRepo()

    LookupLicensesHandler(repo).handle(queries.LookupLicensesQuery(term="cc"))
    GetLicenseHandler(repo).handle(queries.GetLicenseQuery(id=2))
    ListAllEventCategoriesHandler(repo).handle(queries.ListAllEventCategoriesQuery())
    GetEventCategoryHandler(repo).handle(queries.GetEventCategoryQuery(id=3))
    GetEventCategoryByNameHandler(repo).handle(
        queries.GetEventCategoryByNameQuery(name="Other")
    )
    LookupCustomEventCategoriesHandler(repo).handle(
        queries.LookupCustomEventCategoriesQuery(category_set_id=1, term="a")
    )
    GetCustomEventCategoryHandler(repo).handle(
        queries.GetCustomEventCategoryQuery(id=4)
    )

    assert repo.calls[0][1].term == "cc"
    assert [name for name, _ in repo.calls[1:]] == [
        "get_license",
        "all_event_categories",
        "get_event_category",
        "get_event_category_by_name",
        "lookup_custom",
        "get_custom_event_category",
    ]
