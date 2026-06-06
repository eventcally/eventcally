"""Unit tests for app installation command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.install_app_handler import InstallAppHandler
from project.application.command_handlers.uninstall_app_handler import (
    UninstallAppHandler,
)
from project.application.command_handlers.update_app_installation_permissions_handler import (
    UpdateAppInstallationPermissionsHandler,
)
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# InstallAppHandler
# ---------------------------------------------------------------------------


class TestInstallAppHandler:
    def _seed_app(self, uow):
        app = AppAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            name="App",
            app_permissions=["events:read"],
        )
        uow.apps.add(app)
        return app

    def test_creates_installation_and_returns_result(self, uow):
        app = self._seed_app(uow)
        cmd = commands.InstallAppCommand.model_construct(
            actor=Actor(),
            admin_unit_id=2,
            app_id=app.id,
        )

        result = InstallAppHandler().handle(cmd, uow)

        assert result.id > 0
        installation = uow.organization_app_installations.get(result.id)
        assert installation is not None
        assert installation.app_id == app.id
        assert installation.admin_unit_id == 2

    def test_commits(self, uow):
        app = self._seed_app(uow)
        cmd = commands.InstallAppCommand.model_construct(
            actor=Actor(),
            admin_unit_id=2,
            app_id=app.id,
        )

        InstallAppHandler().handle(cmd, uow)

        assert uow.committed

    def test_app_not_found_raises_not_found_error(self, uow):
        cmd = commands.InstallAppCommand.model_construct(
            actor=Actor(),
            admin_unit_id=2,
            app_id=9999,
        )

        with pytest.raises(NotFoundError):
            InstallAppHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UninstallAppHandler
# ---------------------------------------------------------------------------


class TestUninstallAppHandler:
    def _seed_installation(self, uow):
        inst = OrganisationAppInstallationAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            app_id=10,
            permissions=["events:read"],
        )
        uow.organization_app_installations.add(inst)
        return inst

    def test_removes_installation_and_commits(self, uow):
        inst = self._seed_installation(uow)
        inst_id = inst.id

        cmd = commands.UninstallAppCommand.model_construct(actor=Actor(), id=inst_id)
        UninstallAppHandler().handle(cmd, uow)

        assert uow.organization_app_installations.get(inst_id) is None
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UninstallAppCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            UninstallAppHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateAppInstallationPermissionsHandler
# ---------------------------------------------------------------------------


class TestUpdateAppInstallationPermissionsHandler:
    def _seed_installation(self, uow):
        inst = OrganisationAppInstallationAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            app_id=10,
            permissions=["events:read"],
        )
        uow.organization_app_installations.add(inst)
        return inst

    def test_updates_permissions_and_commits(self, uow):
        inst = self._seed_installation(uow)
        cmd = commands.UpdateAppInstallationPermissionsCommand.model_construct(
            actor=Actor(),
            id=inst.id,
            permissions=["events:read", "events:write"],
        )

        UpdateAppInstallationPermissionsHandler().handle(cmd, uow)

        updated = uow.organization_app_installations.get(inst.id)
        assert "events:write" in updated.permissions
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateAppInstallationPermissionsCommand.model_construct(
            actor=Actor(),
            id=9999,
            permissions=[],
        )

        with pytest.raises(NotFoundError):
            UpdateAppInstallationPermissionsHandler().handle(cmd, uow)
