"""App installation query handlers — fake repository, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetAppInstallationHandler,
    GetInstallableAppHandler,
    ListAppInstallationsHandler,
)
from project.application.read_models.app_installation_read_models import (
    AppInstallationReadModel,
    InstallableAppReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_app_installation_read_repository import (
    AbstractAppInstallationReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.application.query_handlers.authz_helpers import ACTOR, authz

PERMISSION = "app_installations:read"
APP = InstallableAppReadModel(id=3, client_name="App")


def _installation(installation_id, admin_unit_id=7):
    return AppInstallationReadModel(
        id=installation_id,
        admin_unit_id=admin_unit_id,
        oauth2_client_id=3,
        oauth2_client=APP,
    )


class FakeRepo(AbstractAppInstallationReadRepository):
    def __init__(self, installations=()):
        self.installations = {i.id: i for i in installations}

    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def list(self, query):
        items = list(self.installations.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get(self, object_id):
        return self.installations.get(object_id)

    def get_installable_app(self, object_id):
        return APP if object_id == 3 else None

    def list_for_user(self, query):
        return Page(items=[], page=1, per_page=20, total=0)

    def list_for_app(self, query):
        items = list(self.installations.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get_for_app(self, app_id, object_id):
        installation = self.installations.get(object_id)
        return installation if installation and app_id == 3 else None


def test_list():
    repo = FakeRepo([_installation(1)])

    assert (
        ListAppInstallationsHandler(repo, authz(PERMISSION))
        .handle(queries.ListAppInstallationsQuery(admin_unit_id=7, actor=ACTOR))
        .total
        == 1
    )
    assert (
        ListAppInstallationsHandler(repo, authz(PERMISSION)).handle(
            queries.ListAppInstallationsQuery(admin_unit_id=8, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        ListAppInstallationsHandler(repo, authz()).handle(
            queries.ListAppInstallationsQuery(admin_unit_id=7, actor=ACTOR)
        )


def test_get():
    handler = GetAppInstallationHandler(
        FakeRepo([_installation(1), _installation(2, admin_unit_id=8)]),
        authz(PERMISSION),
    )

    assert handler.handle(queries.GetAppInstallationQuery(id=1, actor=ACTOR)).id == 1
    assert handler.handle(queries.GetAppInstallationQuery(id=3, actor=ACTOR)) is None
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.GetAppInstallationQuery(id=2, actor=ACTOR))


def test_installable_app_is_public():
    handler = GetInstallableAppHandler(FakeRepo())

    assert handler.handle(queries.GetInstallableAppQuery(id=3)) == APP
    assert handler.handle(queries.GetInstallableAppQuery(id=4)) is None


def test_user_installations_require_the_user():
    from project.application.query_handlers import ListUserAppInstallationsHandler

    handler = ListUserAppInstallationsHandler(FakeRepo(), authz())

    assert (
        handler.handle(
            queries.ListUserAppInstallationsQuery(user_id=7, app_id=3, actor=ACTOR)
        ).total
        == 0
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(
            queries.ListUserAppInstallationsQuery(user_id=8, app_id=3, actor=ACTOR)
        )


def test_app_scoped_installation_queries():
    from project.application.query_handlers import (
        GetAppInstallationForAppHandler,
        ListAppInstallationsForAppHandler,
    )

    repo = FakeRepo([_installation(1)])

    assert (
        ListAppInstallationsForAppHandler(repo)
        .handle(queries.ListAppInstallationsForAppQuery(app_id=3))
        .total
        == 1
    )
    assert (
        GetAppInstallationForAppHandler(repo)
        .handle(queries.GetAppInstallationForAppQuery(app_id=3, id=1))
        .id
        == 1
    )
    assert (
        GetAppInstallationForAppHandler(repo).handle(
            queries.GetAppInstallationForAppQuery(app_id=4, id=1)
        )
        is None
    )
