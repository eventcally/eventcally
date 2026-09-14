"""Unit tests for App command handlers (Create, Update, Delete)."""

import pytest

from project.application import commands
from project.application.command_handlers.create_app_handler import CreateAppHandler
from project.application.command_handlers.delete_app_handler import DeleteAppHandler
from project.application.command_handlers.update_app_handler import UpdateAppHandler
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, grant_permission

# ---------------------------------------------------------------------------
# CreateAppHandler
# ---------------------------------------------------------------------------


class TestCreateAppHandler:
    def test_creates_app_and_returns_result(self, uow):
        grant_permission(uow, 1, "apps:write")
        cmd = commands.CreateAppCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=1,
            name="My App",
            app_permissions=["events:read"],
            scope=None,
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        result = CreateAppHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.apps.get(result.id)
        assert created is not None
        assert created.name == "My App"

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.CreateAppCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=1,
            name="My App",
            app_permissions=["events:read"],
            scope=None,
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        with pytest.raises(UnauthorizedError):
            CreateAppHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateAppHandler
# ---------------------------------------------------------------------------


class TestUpdateAppHandler:
    def _seed(self, uow):
        app = AppAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            name="Old App",
            app_permissions=["events:read"],
        )
        uow.apps.add(app)
        return app

    def test_updates_app(self, uow):
        app = self._seed(uow)
        grant_permission(uow, 1, "apps:write")
        cmd = commands.UpdateAppCommand.model_construct(
            actor=ACTOR,
            id=app.id,
            name="New Name",
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        UpdateAppHandler().handle(cmd, uow)

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateAppCommand.model_construct(
            actor=Actor(),
            id=9999,
            name="x",
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        with pytest.raises(NotFoundError):
            UpdateAppHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        app = self._seed(uow)
        cmd = commands.UpdateAppCommand.model_construct(
            actor=ACTOR,
            id=app.id,
            name="New Name",
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        with pytest.raises(UnauthorizedError):
            UpdateAppHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteAppHandler
# ---------------------------------------------------------------------------


class TestDeleteAppHandler:
    def _seed(self, uow):
        app = AppAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            name="To Delete",
            app_permissions=["events:read"],
        )
        uow.apps.add(app)
        return app

    def test_removes_app(self, uow):
        app = self._seed(uow)
        app_id = app.id
        grant_permission(uow, 1, "apps:write")

        cmd = commands.DeleteAppCommand.model_construct(actor=ACTOR, id=app_id)
        DeleteAppHandler().handle(cmd, uow)

        assert uow.apps.get(app_id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteAppCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            DeleteAppHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        app = self._seed(uow)

        cmd = commands.DeleteAppCommand.model_construct(actor=ACTOR, id=app.id)

        with pytest.raises(UnauthorizedError):
            DeleteAppHandler().handle(cmd, uow)
