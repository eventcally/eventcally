"""Unit tests for RequestUserDeletionHandler and CancelUserDeletionHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.cancel_user_deletion_handler import (
    CancelUserDeletionHandler,
)
from project.application.command_handlers.request_user_deletion_handler import (
    RequestUserDeletionHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID


def _make_user(uow, id=ACTOR_USER_ID, **kwargs):
    user = UserAggregate(id=id, email="user@test.de", locale=None, **kwargs)
    uow.users.add(user)
    return user


class TestRequestUserDeletionHandler:
    def test_requests_deletion(self, uow):
        _make_user(uow)
        cmd = commands.RequestUserDeletionCommand.model_construct(
            actor=ACTOR, id=ACTOR_USER_ID
        )

        RequestUserDeletionHandler().handle(cmd, uow)

        updated = uow.users.get(ACTOR_USER_ID)
        assert updated.deletion_requested_at is not None

    def test_not_found_raises(self, uow):
        cmd = commands.RequestUserDeletionCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            RequestUserDeletionHandler().handle(cmd, uow)

    def test_other_actor_raises_unauthorized_error(self, uow):
        _make_user(uow, id=999)
        cmd = commands.RequestUserDeletionCommand.model_construct(actor=ACTOR, id=999)

        with pytest.raises(UnauthorizedError):
            RequestUserDeletionHandler().handle(cmd, uow)


class TestCancelUserDeletionHandler:
    def test_cancels_deletion(self, uow):
        user = _make_user(uow)
        user.request_deletion(ACTOR)
        uow.users.update(user)

        cmd = commands.CancelUserDeletionCommand.model_construct(
            actor=ACTOR, id=ACTOR_USER_ID
        )

        CancelUserDeletionHandler().handle(cmd, uow)

        updated = uow.users.get(ACTOR_USER_ID)
        assert updated.deletion_requested_at is None

    def test_not_found_raises(self, uow):
        cmd = commands.CancelUserDeletionCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            CancelUserDeletionHandler().handle(cmd, uow)

    def test_other_actor_raises_unauthorized_error(self, uow):
        _make_user(uow, id=999)
        cmd = commands.CancelUserDeletionCommand.model_construct(actor=ACTOR, id=999)

        with pytest.raises(UnauthorizedError):
            CancelUserDeletionHandler().handle(cmd, uow)
