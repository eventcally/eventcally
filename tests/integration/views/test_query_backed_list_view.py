"""The opt-in query-backed path of the modular BaseListView.

Uses the organizer manage list as the vehicle: its view handler is patched to return
a query, and the query handler factory is overridden with a fake, so the page renders
read models from the query bus instead of paginating an ORM query.
"""

from datetime import datetime
from typing import Optional

import pytest
from dependency_injector import providers

from project.application.queries import PageRequest, Query
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.page import Page
from project.views.manage_admin_unit.event_organizer.view_handler import ViewHandler
from project.views.modular.search_definition import KeySearchDefinition
from project.views.modular.sort_definition import KeySortDefinition
from project.views.utils import current_admin_unit


class _OrganizerRow(BaseReadModel):
    id: int
    name: str
    location: Optional[object] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    logo: bool = False
    number_of_events: int = 0
    last_modified_at: datetime = datetime(2026, 1, 1)


class _ListOrganizersQuery(Query[Page[_OrganizerRow]]):
    admin_unit_id: int
    keyword: Optional[str] = None
    page: PageRequest = PageRequest()


class _FakeHandler:
    def __init__(self, page_factory):
        self.page_factory = page_factory
        self.queries = []

    def handle(self, query):
        self.queries.append(query)
        return self.page_factory(query)


@pytest.fixture
def query_backed_organizer_list(app, mocker):
    calls = []

    def create_list_query(self, form, page_request, **kwargs):
        calls.append({"form": form, "page_request": page_request, "kwargs": kwargs})
        return _ListOrganizersQuery(
            admin_unit_id=current_admin_unit.id,
            keyword=form.keyword.data or None,
            page=page_request,
        )

    mocker.patch.object(ViewHandler, "create_list_query", create_list_query)

    def install(page_factory):
        handler = _FakeHandler(page_factory)
        real = app.container.cqrs.query_handler_factory()
        app.container.cqrs.query_handler_factory.override(
            providers.Object(
                lambda query_type: (
                    handler if query_type.__module__ == __name__ else real(query_type)
                )
            )
        )
        return handler

    yield calls, install

    app.container.cqrs.query_handler_factory.reset_override()


def _page_with_rows(query, total, rows):
    return Page[_OrganizerRow](
        items=rows,
        page=query.page.page,
        per_page=query.page.per_page,
        total=total,
    )


def test_renders_items_from_query_bus(
    client, seeder, utils, query_backed_organizer_list
):
    calls, install = query_backed_organizer_list
    _, admin_unit_id = seeder.setup_base()
    handler = install(
        lambda query: _page_with_rows(
            query,
            total=1,
            rows=[_OrganizerRow(id=4711, name="Organizer from the query bus")],
        )
    )

    url = utils.get_url(
        "manage_admin_unit.event_organizers", id=admin_unit_id, keyword="bus"
    )
    response = utils.get_ok(url)

    assert b"Organizer from the query bus" in response.data
    assert len(handler.queries) == 1
    assert handler.queries[0].keyword == "bus"
    assert handler.queries[0].admin_unit_id == admin_unit_id
    # The list's own page size wins over a per_page query arg, as with paginate().
    assert calls[0]["page_request"] == PageRequest(page=1, per_page=50)


def test_passes_page_number_and_renders_pagination(
    client, seeder, utils, query_backed_organizer_list
):
    _, install = query_backed_organizer_list
    _, admin_unit_id = seeder.setup_base()
    handler = install(
        lambda query: _page_with_rows(
            query, total=120, rows=[_OrganizerRow(id=1, name="On page two")]
        )
    )

    url = utils.get_url(
        "manage_admin_unit.event_organizers", id=admin_unit_id, page=2, per_page=5
    )
    response = utils.get_ok(url)

    assert handler.queries[0].page == PageRequest(page=2, per_page=50)
    assert b"On page two" in response.data
    assert b"page=3" in response.data  # next page link
    assert b"page=1" in response.data  # previous / first page link


def test_out_of_range_page_is_not_found(
    client, seeder, utils, query_backed_organizer_list
):
    _, install = query_backed_organizer_list
    _, admin_unit_id = seeder.setup_base()
    install(lambda query: _page_with_rows(query, total=3, rows=[]))

    url = utils.get_url("manage_admin_unit.event_organizers", id=admin_unit_id, page=2)
    response = utils.get(url)

    utils.assert_response_notFound(response)


@pytest.mark.parametrize("page", ["0", "-1", "abc"])
def test_invalid_page_arg_is_not_found(
    client, seeder, utils, query_backed_organizer_list, page
):
    _, install = query_backed_organizer_list
    _, admin_unit_id = seeder.setup_base()
    handler = install(lambda query: _page_with_rows(query, total=0, rows=[]))

    url = utils.get_url(
        "manage_admin_unit.event_organizers", id=admin_unit_id, page=page
    )
    response = utils.get(url)

    utils.assert_response_notFound(response)
    assert handler.queries == []


def test_key_sort_definition():
    ascending = KeySortDefinition("name", label="Name")
    descending = KeySortDefinition("-number_of_events", label="Events")

    assert (ascending.key, ascending.label, ascending.desc) == ("name", "Name", False)
    assert descending.key == "-number_of_events"
    assert descending.desc is True


def test_key_search_definition():
    definition = KeySearchDefinition("name", label="Name")

    assert (definition.key, definition.label) == ("name", "Name")


def test_key_boolean_filter():
    from project.views.modular.filters import BooleanFilter, KeyBooleanFilter

    definition = KeyBooleanFilter("verify", label="Verify")

    assert isinstance(definition, BooleanFilter)
    assert (definition.key, definition.label) == ("verify", "Verify")
    assert [value for value, _ in definition.options] == ["", "1", "0"]


def test_key_enum_filter_keeps_msgids_of_the_named_enum(app):
    from project.domain.models.enums.organization_verification_request_review_status import (
        OrganizationVerificationRequestReviewStatus,
    )
    from project.views.modular.filters import EnumFilter, KeyEnumFilter

    definition = KeyEnumFilter(
        "review_status",
        OrganizationVerificationRequestReviewStatus,
        enum_name="AdminUnitVerificationRequestReviewStatus",
        label="Status",
    )

    assert isinstance(definition, EnumFilter)
    assert definition.key == "review_status"
    assert [value for value, _ in definition.options] == [-1, 1, 2, 3]

    with app.test_request_context(headers={"Accept-Language": "de"}):
        labels = [str(label) for _, label in definition.options]
        assert "AdminUnitVerificationRequestReviewStatus.inbox" not in labels


def test_sort_key_or_none():
    from project.application.queries import ApiKeySort
    from project.views.modular.sort_definition import sort_key_or_none

    assert sort_key_or_none(ApiKeySort, "name") is ApiKeySort.name
    assert sort_key_or_none(ApiKeySort, "bogus") is None
    assert sort_key_or_none(ApiKeySort, None) is None
