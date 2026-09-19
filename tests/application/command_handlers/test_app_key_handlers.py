"""Unit tests for AppKey command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_app_key_handler import (
    CreateAppKeyHandler,
)
from project.application.command_handlers.delete_app_key_handler import (
    DeleteAppKeyHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.aggregates.app_key_aggregate import AppKeyAggregate
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, FakeAppKeyGenerator, grant_permission

ADMIN_UNIT_ID = 1
APP_ID = 2


def _handler():
    return CreateAppKeyHandler(app_key_generator=FakeAppKeyGenerator())


def _seed_app(uow, admin_unit_id=ADMIN_UNIT_ID, app_id=APP_ID):
    app = AppAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="App",
        app_permissions=set(),
        client_id="client-id",
        client_secret="client-secret",
    )
    app.id = app_id
    uow.apps.add(app)
    return app


def _seed_app_key(uow, admin_unit_id=ADMIN_UNIT_ID, app_id=APP_ID):
    app_key = AppKeyAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        app_id=app_id,
        checksum="existing-checksum",
        kid="existing-kid",
        public_key="existing-public-key",
    )
    uow.app_keys.add(app_key)
    return app_key


class TestCreateAppKeyHandler:
    def test_creates_app_key_and_returns_result(self, uow):
        _seed_app(uow)
        grant_permission(uow, ADMIN_UNIT_ID, "app_keys:write")
        cmd = commands.CreateAppKeyCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, app_id=APP_ID
        )

        result = _handler().handle(cmd, uow)

        assert isinstance(result, commands.CreateAppKeyCommandResult)
        assert result.private_pem == "fake-private-pem"

        app_key = uow.app_keys.get(result.id)
        assert app_key.admin_unit_id == ADMIN_UNIT_ID
        assert app_key.app_id == APP_ID
        assert app_key.checksum == "fake-checksum"
        assert app_key.kid == "fake-kid"
        assert app_key.public_key == "fake-public-key"

    def test_unauthorized_actor_raises(self, uow):
        _seed_app(uow)
        cmd = commands.CreateAppKeyCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, app_id=APP_ID
        )

        with pytest.raises(UnauthorizedError):
            _handler().handle(cmd, uow)

    def test_app_of_other_admin_unit_raises(self, uow):
        _seed_app(uow, admin_unit_id=ADMIN_UNIT_ID + 1)
        grant_permission(uow, ADMIN_UNIT_ID, "app_keys:write")
        cmd = commands.CreateAppKeyCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, app_id=APP_ID
        )

        with pytest.raises(UnauthorizedError):
            _handler().handle(cmd, uow)

    def test_unknown_app_raises(self, uow):
        grant_permission(uow, ADMIN_UNIT_ID, "app_keys:write")
        cmd = commands.CreateAppKeyCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, app_id=999
        )

        with pytest.raises(NotFoundError):
            _handler().handle(cmd, uow)


class TestDeleteAppKeyHandler:
    def test_removes_app_key(self, uow):
        app_key = _seed_app_key(uow)
        grant_permission(uow, ADMIN_UNIT_ID, "app_keys:write")
        cmd = commands.DeleteAppKeyCommand.model_construct(actor=ACTOR, id=app_key.id)

        DeleteAppKeyHandler().handle(cmd, uow)

        assert uow.app_keys.get(app_key.id) is None

    def test_not_found_raises(self, uow):
        cmd = commands.DeleteAppKeyCommand.model_construct(actor=ACTOR, id=999)
        with pytest.raises(NotFoundError):
            DeleteAppKeyHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        app_key = _seed_app_key(uow)
        cmd = commands.DeleteAppKeyCommand.model_construct(actor=ACTOR, id=app_key.id)
        with pytest.raises(UnauthorizedError):
            DeleteAppKeyHandler().handle(cmd, uow)
