"""The opt-in query-backed path of the modular BaseListView.

Uses the app manage list as the vehicle: its view handler is
patched to return a query, and the query handler factory is overridden with a fake, so the page renders
read models from the query bus instead of paginating an ORM query.
"""

from datetime import datetime

import pytest
from dependency_injector import providers

from project.application.queries import PageRequest, Query
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.page import Page
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.views.manage_admin_unit.app.view_handler import (
    AppViewHandler as ViewHandler,
)


class _AppRow(BaseReadModel):
    id: int
    client_name: str
    created_at: datetime = datetime(2026, 1, 1)


class _ListAppsQuery(Query[Page[_AppRow]]):
    admin_unit_id: int
    page: PageRequest = PageRequest()


class _FakeHandler:
    def __init__(self, page_factory):
        self.page_factory = page_factory
        self.queries = []

    def handle(self, query):
        self.queries.append(query)
        return self.page_factory(query)


@pytest.fixture
def query_backed_app_list(app, mocker):
    calls = []

    def create_list_query(self, page_request, **kwargs):
        calls.append({"page_request": page_request, "kwargs": kwargs})
        return _ListAppsQuery(
            admin_unit_id=current_admin_unit.id,
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
    return Page[_AppRow](
        items=rows,
        page=query.page.page,
        per_page=query.page.per_page,
        total=total,
    )


def test_renders_items_from_query_bus(client, seeder, utils, query_backed_app_list):
    calls, install = query_backed_app_list
    _, admin_unit_id = seeder.setup_base()
    handler = install(
        lambda query: _page_with_rows(
            query,
            total=1,
            rows=[_AppRow(id=4711, client_name="App from the query bus")],
        )
    )

    url = utils.get_url("manage_admin_unit.apps", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b"App from the query bus" in response.data
    assert len(handler.queries) == 1
    assert handler.queries[0].admin_unit_id == admin_unit_id
    # The list's own page size wins over a per_page query arg, as with paginate().
    assert calls[0]["page_request"] == PageRequest(page=1, per_page=20)


def test_passes_page_number_and_renders_pagination(
    client, seeder, utils, query_backed_app_list
):
    _, install = query_backed_app_list
    _, admin_unit_id = seeder.setup_base()
    handler = install(
        lambda query: _page_with_rows(
            query, total=120, rows=[_AppRow(id=1, client_name="On page two")]
        )
    )

    url = utils.get_url(
        "manage_admin_unit.apps",
        id=admin_unit_id,
        page=2,
        per_page=5,
    )
    response = utils.get_ok(url)

    assert handler.queries[0].page == PageRequest(page=2, per_page=20)
    assert b"On page two" in response.data
    assert b"page=3" in response.data  # next page link
    assert b"page=1" in response.data  # previous / first page link


def test_out_of_range_page_is_not_found(client, seeder, utils, query_backed_app_list):
    _, install = query_backed_app_list
    _, admin_unit_id = seeder.setup_base()
    install(lambda query: _page_with_rows(query, total=3, rows=[]))

    url = utils.get_url("manage_admin_unit.apps", id=admin_unit_id, page=2)
    response = utils.get(url)

    utils.assert_response_notFound(response)


@pytest.mark.parametrize("page", ["0", "-1", "abc"])
def test_invalid_page_arg_is_not_found(
    client, seeder, utils, query_backed_app_list, page
):
    _, install = query_backed_app_list
    _, admin_unit_id = seeder.setup_base()
    handler = install(lambda query: _page_with_rows(query, total=0, rows=[]))

    url = utils.get_url("manage_admin_unit.apps", id=admin_unit_id, page=page)
    response = utils.get(url)

    utils.assert_response_notFound(response)
    assert handler.queries == []
