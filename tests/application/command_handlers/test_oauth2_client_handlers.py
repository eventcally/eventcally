"""Unit tests for OAuth2Client command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_oauth2_client_handler import (
    CreateOAuth2ClientHandler,
)
from project.application.command_handlers.delete_oauth2_client_handler import (
    DeleteOAuth2ClientHandler,
)
from project.application.command_handlers.update_oauth2_client_handler import (
    UpdateOAuth2ClientHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)
from project.domain.models.entities.actor import Actor
from tests.application.conftest import (
    ACTOR,
    ACTOR_USER_ID,
    FakeOAuth2ClientCredentialsGenerator,
    grant_permission,
)

OTHER_USER_ID = 2


def _seed_oauth2_client(uow, user_id=None, admin_unit_id=None, name="Existing Client"):
    oauth2_client = OAuth2ClientAggregate.create(
        actor=Actor(),
        name=name,
        client_id="existing-client-id",
        client_secret="existing-client-secret",
        user_id=user_id,
        admin_unit_id=admin_unit_id,
    )
    uow.oauth2_clients.add(oauth2_client)
    return oauth2_client


# ---------------------------------------------------------------------------
# CreateOAuth2ClientHandler
# ---------------------------------------------------------------------------


class TestCreateOAuth2ClientHandler:
    def _handler(self):
        return CreateOAuth2ClientHandler(
            credentials_generator=FakeOAuth2ClientCredentialsGenerator()
        )

    def test_creates_user_owned_client_and_returns_result(self, uow):
        cmd = commands.CreateOAuth2ClientCommand.model_construct(
            actor=ACTOR, name="My Client", user_id=ACTOR_USER_ID
        )

        result = self._handler().handle(cmd, uow)

        assert result.id > 0
        assert result.client_id == "fake-client-id"
        assert result.client_secret == "fake-client-secret"
        created = uow.oauth2_clients.get(result.id)
        assert created is not None
        assert created.name == "My Client"
        assert created.client_id == "fake-client-id"
        assert created.client_secret == "fake-client-secret"
        assert created.user_id == ACTOR_USER_ID
        assert created.admin_unit_id is None

    def test_creates_admin_unit_owned_client_and_returns_result(self, uow):
        grant_permission(uow, 1, "oauth2_clients:write")
        cmd = commands.CreateOAuth2ClientCommand.model_construct(
            actor=ACTOR, name="Org Client", admin_unit_id=1
        )

        result = self._handler().handle(cmd, uow)

        created = uow.oauth2_clients.get(result.id)
        assert created.admin_unit_id == 1
        assert created.user_id is None

    def test_user_owned_by_other_user_raises_unauthorized_error(self, uow):
        cmd = commands.CreateOAuth2ClientCommand.model_construct(
            actor=ACTOR, name="My Client", user_id=OTHER_USER_ID
        )

        with pytest.raises(UnauthorizedError):
            self._handler().handle(cmd, uow)

    def test_admin_unit_owned_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.CreateOAuth2ClientCommand.model_construct(
            actor=ACTOR, name="Org Client", admin_unit_id=1
        )

        with pytest.raises(UnauthorizedError):
            self._handler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateOAuth2ClientHandler
# ---------------------------------------------------------------------------


class TestUpdateOAuth2ClientHandler:
    def test_updates_user_owned_client(self, uow):
        oauth2_client = _seed_oauth2_client(uow, user_id=ACTOR_USER_ID)
        cmd = commands.UpdateOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id, name="New Name"
        )

        UpdateOAuth2ClientHandler().handle(cmd, uow)

        assert uow.oauth2_clients.get(oauth2_client.id).name == "New Name"

    def test_updates_admin_unit_owned_client(self, uow):
        oauth2_client = _seed_oauth2_client(uow, admin_unit_id=1)
        grant_permission(uow, 1, "oauth2_clients:write")
        cmd = commands.UpdateOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id, name="New Name"
        )

        UpdateOAuth2ClientHandler().handle(cmd, uow)

        assert uow.oauth2_clients.get(oauth2_client.id).name == "New Name"

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateOAuth2ClientCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            UpdateOAuth2ClientHandler().handle(cmd, uow)

    def test_user_owned_by_other_user_raises_unauthorized_error(self, uow):
        oauth2_client = _seed_oauth2_client(uow, user_id=OTHER_USER_ID)
        cmd = commands.UpdateOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id, name="New Name"
        )

        with pytest.raises(UnauthorizedError):
            UpdateOAuth2ClientHandler().handle(cmd, uow)

    def test_admin_unit_owned_without_permission_raises_unauthorized_error(self, uow):
        oauth2_client = _seed_oauth2_client(uow, admin_unit_id=1)
        cmd = commands.UpdateOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id, name="New Name"
        )

        with pytest.raises(UnauthorizedError):
            UpdateOAuth2ClientHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteOAuth2ClientHandler
# ---------------------------------------------------------------------------


class TestDeleteOAuth2ClientHandler:
    def test_removes_user_owned_client(self, uow):
        oauth2_client = _seed_oauth2_client(uow, user_id=ACTOR_USER_ID)
        cmd = commands.DeleteOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id
        )

        DeleteOAuth2ClientHandler().handle(cmd, uow)

        assert uow.oauth2_clients.get(oauth2_client.id) is None

    def test_removes_admin_unit_owned_client(self, uow):
        oauth2_client = _seed_oauth2_client(uow, admin_unit_id=1)
        grant_permission(uow, 1, "oauth2_clients:write")
        cmd = commands.DeleteOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id
        )

        DeleteOAuth2ClientHandler().handle(cmd, uow)

        assert uow.oauth2_clients.get(oauth2_client.id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteOAuth2ClientCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            DeleteOAuth2ClientHandler().handle(cmd, uow)

    def test_user_owned_by_other_user_raises_unauthorized_error(self, uow):
        oauth2_client = _seed_oauth2_client(uow, user_id=OTHER_USER_ID)
        cmd = commands.DeleteOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id
        )

        with pytest.raises(UnauthorizedError):
            DeleteOAuth2ClientHandler().handle(cmd, uow)

    def test_admin_unit_owned_without_permission_raises_unauthorized_error(self, uow):
        oauth2_client = _seed_oauth2_client(uow, admin_unit_id=1)
        cmd = commands.DeleteOAuth2ClientCommand.model_construct(
            actor=ACTOR, id=oauth2_client.id
        )

        with pytest.raises(UnauthorizedError):
            DeleteOAuth2ClientHandler().handle(cmd, uow)
