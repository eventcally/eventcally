"""API key query handlers — fake repository and reader, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetApiKeyHandler,
    ListOrganizationApiKeysHandler,
    ListUserApiKeysHandler,
)
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_api_key_read_repository import (
    AbstractApiKeyReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.application.query_handlers.authz_helpers import ACTOR, authz

PERMISSION = "api_keys:read"


def _key(key_id, admin_unit_id=None, user_id=None):
    return ApiKeyReadModel(
        id=key_id,
        name="Key",
        admin_unit_id=admin_unit_id,
        user_id=user_id,
        rate_limit_value="500/hour",
    )


class FakeRepo(AbstractApiKeyReadRepository):
    def __init__(self, organization_ids=(), keys=()):
        self.organization_ids = set(organization_ids)
        self.keys = {key.id: key for key in keys}
        self.queries = []

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organization_ids

    def list(self, query):
        self.queries.append(query)
        items = list(self.keys.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get(self, object_id):
        return self.keys.get(object_id)


def test_read_model_is_a_rate_limit_provider():
    key = _key(3, user_id=7)

    assert key.get_rate_limit_key() == "apikey-3"
    assert key.get_rate_limit_value() == "500/hour"


def test_organization_list():
    handler = ListOrganizationApiKeysHandler(
        FakeRepo(organization_ids=[7], keys=[_key(1, admin_unit_id=7)]),
        authz(PERMISSION),
    )

    page = handler.handle(
        queries.ListOrganizationApiKeysQuery(admin_unit_id=7, actor=ACTOR)
    )
    assert [item.id for item in page.items] == [1]
    assert (
        handler.handle(
            queries.ListOrganizationApiKeysQuery(admin_unit_id=8, actor=ACTOR)
        )
        is None
    )

    with pytest.raises(UnauthorizedError):
        ListOrganizationApiKeysHandler(FakeRepo(organization_ids=[7]), authz()).handle(
            queries.ListOrganizationApiKeysQuery(admin_unit_id=7, actor=ACTOR)
        )


def test_user_list():
    handler = ListUserApiKeysHandler(FakeRepo(keys=[_key(1, user_id=7)]), authz())

    page = handler.handle(queries.ListUserApiKeysQuery(user_id=7, actor=ACTOR))
    assert [item.id for item in page.items] == [1]

    with pytest.raises(UnauthorizedError):
        handler.handle(queries.ListUserApiKeysQuery(user_id=8, actor=ACTOR))


@pytest.mark.parametrize(
    "key, permitted",
    [
        (_key(1, admin_unit_id=7), True),
        (_key(1, admin_unit_id=8), False),
        (_key(1, user_id=7), True),
        (_key(1, user_id=8), False),
    ],
)
def test_get_authorizes_by_owner(key, permitted):
    handler = GetApiKeyHandler(FakeRepo(keys=[key]), authz(PERMISSION))
    query = queries.GetApiKeyQuery(id=1, actor=ACTOR)

    if permitted:
        assert handler.handle(query) == key
    else:
        with pytest.raises(UnauthorizedError):
            handler.handle(query)


def test_get_unknown_returns_none():
    handler = GetApiKeyHandler(FakeRepo(), authz())

    assert handler.handle(queries.GetApiKeyQuery(id=1, actor=ACTOR)) is None
