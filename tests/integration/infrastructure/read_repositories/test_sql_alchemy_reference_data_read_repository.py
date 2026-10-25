"""SqlAlchemyReferenceDataReadRepository lookups against the database."""

import pytest

from project.application.queries import (
    ListCustomEventCategoriesQuery,
    ListCustomEventCategorySetsQuery,
    ListEventCategoriesQuery,
    ListLicensesQuery,
    LookupCustomEventCategoriesQuery,
    LookupLicensesQuery,
    PageRequest,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.reference_data_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def test_lookup_licenses_orders_by_sort_and_filters_code_or_name(read_repo):
    page = read_repo("lookup_licenses", LookupLicensesQuery())
    assert page.total == len(page.items) > 3
    assert page.items[0].code == "CC0 1.0"

    page = read_repo("lookup_licenses", LookupLicensesQuery(term="nothing-like"))
    assert page.items == []

    page = read_repo("lookup_licenses", LookupLicensesQuery(term="BY-sa"))
    assert [item.code for item in page.items] == ["CC BY-SA 4.0"]

    page = read_repo("lookup_licenses", LookupLicensesQuery(term="zero"))
    assert [item.code for item in page.items] == ["CC0 1.0"]


def test_lookup_licenses_pages(read_repo):
    page = read_repo(
        "lookup_licenses", LookupLicensesQuery(page=PageRequest(page=2, per_page=2))
    )

    assert len(page.items) == 2
    assert page.has_prev


def test_get_license(read_repo):
    license = read_repo("lookup_licenses", LookupLicensesQuery()).items[1]

    assert read_repo("get_license", license.id) == license
    assert read_repo("get_license", 4711) is None


def test_event_categories(read_repo):
    categories = read_repo("list_all_event_categories")

    assert len(categories) > 10
    first = categories[0]
    assert read_repo("get_event_category", first.id) == first
    assert read_repo("get_event_category", 4711) is None
    assert read_repo("get_event_category_by_name", first.name) == first
    assert read_repo("get_event_category_by_name", "No such category") is None


def test_lookup_custom_event_categories(app, db, read_repo, seeder):
    set_id, category_id = seeder.get_one_custom_event_category_set()

    page = read_repo(
        "lookup_custom_event_categories",
        LookupCustomEventCategoriesQuery(category_set_id=set_id),
    )
    assert page.total >= 1
    assert category_id in [item.id for item in page.items]
    assert [item.name for item in page.items] == sorted(
        item.name for item in page.items
    )

    page = read_repo(
        "lookup_custom_event_categories",
        LookupCustomEventCategoriesQuery(category_set_id=set_id, term="nothing-like"),
    )
    assert page.items == []

    page = read_repo(
        "lookup_custom_event_categories",
        LookupCustomEventCategoriesQuery(category_set_id=4711),
    )
    assert page.items == []


def test_get_custom_event_category(read_repo, seeder):
    _, category_id = seeder.get_one_custom_event_category_set()

    category = read_repo("get_custom_event_category", category_id)

    assert category.id == category_id
    assert category.label_or_name == (category.label or category.name)
    assert read_repo("get_custom_event_category", 4711) is None


def test_list_reference_data(app, db, read_repo, seeder):
    set_id, category_id = seeder.get_one_custom_event_category_set()

    licenses = read_repo("list_licenses", ListLicensesQuery())
    categories = read_repo("list_event_categories", ListEventCategoriesQuery())
    sets = read_repo(
        "list_custom_event_category_sets", ListCustomEventCategorySetsQuery()
    )
    custom_categories = read_repo(
        "list_custom_event_categories",
        ListCustomEventCategoriesQuery(category_set_id=set_id),
    )

    assert licenses.total == len(licenses.items) > 3
    assert [item.id for item in licenses.items] == sorted(
        item.id for item in licenses.items
    )
    assert licenses.items[0].code == "CC0 1.0"
    assert categories.total > 1
    assert "Other" in [item.name for item in categories.items]
    assert set_id in [item.id for item in sets.items]
    assert category_id in [item.id for item in custom_categories.items]
