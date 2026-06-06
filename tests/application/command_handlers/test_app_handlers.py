"""Unit tests for App command handlers (Create, Update, Delete)."""

import pytest

from project.application import commands
from project.application.command_handlers.create_app_handler import CreateAppHandler
from project.application.command_handlers.delete_app_handler import DeleteAppHandler
from project.application.command_handlers.update_app_handler import UpdateAppHandler
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# CreateAppHandler
# ---------------------------------------------------------------------------


class TestCreateAppHandler:
    def test_creates_app_and_returns_result(self, uow):
        cmd = commands.CreateAppCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="My App",
            app_permissions=["events:read"],
            redirect_uris=None,
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

    def test_commits(self, uow):
        cmd = commands.CreateAppCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="My App",
            app_permissions=["events:read"],
            redirect_uris=None,
            scope=None,
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        CreateAppHandler().handle(cmd, uow)

        assert uow.committed


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

    def test_updates_app_and_commits(self, uow):
        app = self._seed(uow)
        cmd = commands.UpdateAppCommand.model_construct(
            actor=Actor(),
            id=app.id,
            name="New Name",
            description=None,
            homepage_url=None,
            setup_url=None,
            webhook=None,
        )

        UpdateAppHandler().handle(cmd, uow)

        assert uow.committed

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


# ---------------------------------------------------------------------------
# DeleteAppHandler
# ---------------------------------------------------------------------------


class TestDeleteAppHandler:
    def test_removes_app_and_commits(self, uow):
        app = AppAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            name="To Delete",
            app_permissions=["events:read"],
        )
        uow.apps.add(app)
        app_id = app.id

        cmd = commands.DeleteAppCommand.model_construct(actor=Actor(), id=app_id)
        DeleteAppHandler().handle(cmd, uow)

        assert uow.apps.get(app_id) is None
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteAppCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            DeleteAppHandler().handle(cmd, uow)
