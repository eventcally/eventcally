"""OAuth2 client and app query handlers — fake repository and reader, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetAppHandler,
    GetOAuth2ClientHandler,
    ListAppsHandler,
    ListOrganizationOAuth2ClientsHandler,
    ListUserOAuth2ClientsHandler,
)
from project.application.read_models.oauth2_client_read_models import (
    AppReadModel,
    OAuth2ClientReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_oauth2_client_read_repository import (
    AbstractOAuth2ClientReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.application.query_handlers.authz_helpers import ACTOR, authz


def _client(client_id, admin_unit_id=None, user_id=None):
    return OAuth2ClientReadModel(
        id=client_id, client_id="abc", admin_unit_id=admin_unit_id, user_id=user_id
    )


def _app(app_id, admin_unit_id=7):
    return AppReadModel(id=app_id, client_id="abc", admin_unit_id=admin_unit_id)


class FakeRepo(AbstractOAuth2ClientReadRepository):
    def __init__(self, organization_ids=(), clients=(), apps=()):
        self.organization_ids = set(organization_ids)
        self.clients = {c.id: c for c in clients}
        self.apps = {a.id: a for a in apps}

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organization_ids

    def list(self, query):
        items = list(
            (
                self.apps if isinstance(query, queries.ListAppsQuery) else self.clients
            ).values()
        )
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get(self, object_id):
        return self.clients.get(object_id)

    def get_app(self, object_id):
        return self.apps.get(object_id)


def test_organization_client_list_requires_permission():
    repo = FakeRepo(organization_ids=[7], clients=[_client(1, admin_unit_id=7)])

    page = ListOrganizationOAuth2ClientsHandler(
        repo, authz("oauth2_clients:read")
    ).handle(queries.ListOrganizationOAuth2ClientsQuery(admin_unit_id=7, actor=ACTOR))
    assert [item.id for item in page.items] == [1]

    with pytest.raises(UnauthorizedError):
        ListOrganizationOAuth2ClientsHandler(repo, authz("apps:read")).handle(
            queries.ListOrganizationOAuth2ClientsQuery(admin_unit_id=7, actor=ACTOR)
        )


def test_user_client_list():
    handler = ListUserOAuth2ClientsHandler(
        FakeRepo(clients=[_client(1, user_id=7)]), authz()
    )

    assert (
        handler.handle(queries.ListUserOAuth2ClientsQuery(user_id=7, actor=ACTOR)).total
        == 1
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.ListUserOAuth2ClientsQuery(user_id=8, actor=ACTOR))


@pytest.mark.parametrize(
    "client, permitted",
    [
        (_client(1, admin_unit_id=7), True),
        (_client(1, admin_unit_id=8), False),
        (_client(1, user_id=7), True),
        (_client(1, user_id=8), False),
    ],
)
def test_get_client_authorizes_by_owner(client, permitted):
    handler = GetOAuth2ClientHandler(
        FakeRepo(clients=[client]), authz("oauth2_clients:read")
    )
    query = queries.GetOAuth2ClientQuery(id=1, actor=ACTOR)

    if permitted:
        assert handler.handle(query) == client
    else:
        with pytest.raises(UnauthorizedError):
            handler.handle(query)

    assert (
        GetOAuth2ClientHandler(FakeRepo(), authz()).handle(
            queries.GetOAuth2ClientQuery(id=2, actor=ACTOR)
        )
        is None
    )


def test_apps():
    repo = FakeRepo(organization_ids=[7], apps=[_app(1), _app(2, admin_unit_id=8)])

    page = ListAppsHandler(repo, authz("apps:read")).handle(
        queries.ListAppsQuery(admin_unit_id=7, actor=ACTOR)
    )
    assert page.total == 2

    handler = GetAppHandler(repo, authz("apps:read"))
    assert handler.handle(queries.GetAppQuery(id=1, actor=ACTOR)) == _app(1)
    assert handler.handle(queries.GetAppQuery(id=3, actor=ACTOR)) is None
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.GetAppQuery(id=2, actor=ACTOR))


@pytest.mark.parametrize(
    "handler_class, query_class",
    [
        (ListAppsHandler, queries.ListAppsQuery),
        (
            ListOrganizationOAuth2ClientsHandler,
            queries.ListOrganizationOAuth2ClientsQuery,
        ),
    ],
)
def test_lists_of_unknown_organization_return_none(handler_class, query_class):
    handler = handler_class(FakeRepo(organization_ids=[7]), authz("apps:read"))

    assert handler.handle(query_class(admin_unit_id=8, actor=ACTOR)) is None
