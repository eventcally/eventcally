"""Tests for micro-gaps in command handlers – NotFoundError branches."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from project.domain import commands
from project.domain.errors import NotFoundError
from project.service_layer.command_handlers.app_utils import ensure_app_exists
from project.service_layer.command_handlers.uninstall_app_handler import (
    UninstallAppHandler,
)
from project.service_layer.command_handlers.update_app_installation_permissions_handler import (
    UpdateAppInstallationPermissionsHandler,
)


class _FakeUow:
    def __init__(self, app_installation=None, app=None):
        self.apps = SimpleNamespace(
            get_app_installation=Mock(return_value=app_installation),
            get=Mock(return_value=app),
        )
        self.commit = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def test_uninstall_app_handler_raises_not_found_when_installation_missing():
    handler = UninstallAppHandler()
    uow = _FakeUow(app_installation=None)
    cmd = commands.UninstallAppCommand.model_construct(id=999)

    with pytest.raises(NotFoundError):
        handler.handle(cmd, uow)


def test_update_app_installation_permissions_handler_raises_not_found_when_missing():
    handler = UpdateAppInstallationPermissionsHandler()
    uow = _FakeUow(app_installation=None)
    cmd = commands.UpdateAppInstallationPermissionsCommand.model_construct(
        id=999, permissions=[]
    )

    with pytest.raises(NotFoundError):
        handler.handle(cmd, uow)


def test_ensure_app_exists_raises_not_found_when_app_missing():
    uow = _FakeUow(app=None)

    with pytest.raises(NotFoundError):
        ensure_app_exists(999, uow)


def test_ensure_app_exists_returns_app_when_found():
    fake_app = SimpleNamespace(id=1)
    uow = _FakeUow(app=fake_app)

    result = ensure_app_exists(1, uow)
    assert result is fake_app
