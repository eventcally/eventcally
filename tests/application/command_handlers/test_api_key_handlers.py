"""Unit tests for API key command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_api_key_handler import (
    CreateApiKeyHandler,
)
from project.application.command_handlers.delete_api_key_handler import (
    DeleteApiKeyHandler,
)
from project.application.command_handlers.update_api_key_handler import (
    UpdateApiKeyHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor
from tests.application.conftest import (
    ACTOR,
    ACTOR_USER_ID,
    FakeApiKeyGenerator,
    grant_permission,
)

OTHER_USER_ID = 2


def _seed_user(uow, user_id=ACTOR_USER_ID, max_api_keys=1):
    uow.users.add(
        UserAggregate(
            id=user_id, email="user@test.de", locale=None, max_api_keys=max_api_keys
        )
    )


def _seed_org(uow, admin_unit_id=1, max_api_keys=1):
    uow.organizations.add(
        OrganizationAggregate(id=admin_unit_id, max_api_keys=max_api_keys)
    )


def _seed_api_key(uow, user_id=None, admin_unit_id=None, name="Existing Key"):
    api_key = ApiKeyAggregate.create(
        actor=Actor(),
        name=name,
        key_hash="existing-hash",
        user_id=user_id,
        admin_unit_id=admin_unit_id,
    )
    uow.api_keys.add(api_key)
    return api_key


# ---------------------------------------------------------------------------
# CreateApiKeyHandler
# ---------------------------------------------------------------------------


class TestCreateApiKeyHandler:
    def _handler(self):
        return CreateApiKeyHandler(api_key_generator=FakeApiKeyGenerator())

    def test_creates_user_owned_key_and_returns_result(self, uow):
        _seed_user(uow)
        cmd = commands.CreateApiKeyCommand.model_construct(
            actor=ACTOR, name="My Key", user_id=ACTOR_USER_ID
        )

        result = self._handler().handle(cmd, uow)

        assert result.id > 0
        assert result.key == "plaintext-key"
        created = uow.api_keys.get(result.id)
        assert created is not None
        assert created.name == "My Key"
        assert created.key_hash == "hashed-key"
        assert created.user_id == ACTOR_USER_ID
        assert created.admin_unit_id is None

    def test_creates_admin_unit_owned_key_and_returns_result(self, uow):
        _seed_org(uow, admin_unit_id=1)
        grant_permission(uow, 1, "api_keys:write")
        cmd = commands.CreateApiKeyCommand.model_construct(
            actor=ACTOR, name="Org Key", admin_unit_id=1
        )

        result = self._handler().handle(cmd, uow)

        created = uow.api_keys.get(result.id)
        assert created.admin_unit_id == 1
        assert created.user_id is None

    def test_user_owned_by_other_user_raises_unauthorized_error(self, uow):
        cmd = commands.CreateApiKeyCommand.model_construct(
            actor=ACTOR, name="My Key", user_id=OTHER_USER_ID
        )

        with pytest.raises(UnauthorizedError):
            self._handler().handle(cmd, uow)

    def test_admin_unit_owned_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.CreateApiKeyCommand.model_construct(
            actor=ACTOR, name="Org Key", admin_unit_id=1
        )

        with pytest.raises(UnauthorizedError):
            self._handler().handle(cmd, uow)

    def test_max_api_keys_reached_raises_constraint_error(self, uow):
        _seed_user(uow, max_api_keys=1)
        _seed_api_key(uow, user_id=ACTOR_USER_ID)
        cmd = commands.CreateApiKeyCommand.model_construct(
            actor=ACTOR, name="One Too Many", user_id=ACTOR_USER_ID
        )

        with pytest.raises(ConstraintError):
            self._handler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateApiKeyHandler
# ---------------------------------------------------------------------------


class TestUpdateApiKeyHandler:
    def test_updates_user_owned_key(self, uow):
        api_key = _seed_api_key(uow, user_id=ACTOR_USER_ID)
        cmd = commands.UpdateApiKeyCommand.model_construct(
            actor=ACTOR, id=api_key.id, name="New Name"
        )

        UpdateApiKeyHandler().handle(cmd, uow)

        assert uow.api_keys.get(api_key.id).name == "New Name"

    def test_updates_admin_unit_owned_key(self, uow):
        api_key = _seed_api_key(uow, admin_unit_id=1)
        grant_permission(uow, 1, "api_keys:write")
        cmd = commands.UpdateApiKeyCommand.model_construct(
            actor=ACTOR, id=api_key.id, name="New Name"
        )

        UpdateApiKeyHandler().handle(cmd, uow)

        assert uow.api_keys.get(api_key.id).name == "New Name"

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateApiKeyCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            UpdateApiKeyHandler().handle(cmd, uow)

    def test_user_owned_by_other_user_raises_unauthorized_error(self, uow):
        api_key = _seed_api_key(uow, user_id=OTHER_USER_ID)
        cmd = commands.UpdateApiKeyCommand.model_construct(
            actor=ACTOR, id=api_key.id, name="New Name"
        )

        with pytest.raises(UnauthorizedError):
            UpdateApiKeyHandler().handle(cmd, uow)

    def test_admin_unit_owned_without_permission_raises_unauthorized_error(self, uow):
        api_key = _seed_api_key(uow, admin_unit_id=1)
        cmd = commands.UpdateApiKeyCommand.model_construct(
            actor=ACTOR, id=api_key.id, name="New Name"
        )

        with pytest.raises(UnauthorizedError):
            UpdateApiKeyHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteApiKeyHandler
# ---------------------------------------------------------------------------


class TestDeleteApiKeyHandler:
    def test_removes_user_owned_key(self, uow):
        api_key = _seed_api_key(uow, user_id=ACTOR_USER_ID)
        cmd = commands.DeleteApiKeyCommand.model_construct(actor=ACTOR, id=api_key.id)

        DeleteApiKeyHandler().handle(cmd, uow)

        assert uow.api_keys.get(api_key.id) is None

    def test_removes_admin_unit_owned_key(self, uow):
        api_key = _seed_api_key(uow, admin_unit_id=1)
        grant_permission(uow, 1, "api_keys:write")
        cmd = commands.DeleteApiKeyCommand.model_construct(actor=ACTOR, id=api_key.id)

        DeleteApiKeyHandler().handle(cmd, uow)

        assert uow.api_keys.get(api_key.id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteApiKeyCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            DeleteApiKeyHandler().handle(cmd, uow)

    def test_user_owned_by_other_user_raises_unauthorized_error(self, uow):
        api_key = _seed_api_key(uow, user_id=OTHER_USER_ID)
        cmd = commands.DeleteApiKeyCommand.model_construct(actor=ACTOR, id=api_key.id)

        with pytest.raises(UnauthorizedError):
            DeleteApiKeyHandler().handle(cmd, uow)

    def test_admin_unit_owned_without_permission_raises_unauthorized_error(self, uow):
        api_key = _seed_api_key(uow, admin_unit_id=1)
        cmd = commands.DeleteApiKeyCommand.model_construct(actor=ACTOR, id=api_key.id)

        with pytest.raises(UnauthorizedError):
            DeleteApiKeyHandler().handle(cmd, uow)
