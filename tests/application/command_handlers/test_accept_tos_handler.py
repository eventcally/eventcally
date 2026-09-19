"""Unit tests for AcceptTosHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.accept_tos_handler import AcceptTosHandler
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID


def _make_user(uow, id=ACTOR_USER_ID, **kwargs):
    user = UserAggregate(id=id, email="user@test.de", locale=None, **kwargs)
    uow.users.add(user)
    return user


class TestAcceptTosHandler:
    def test_accepts_tos(self, uow):
        _make_user(uow)
        cmd = commands.AcceptTosCommand.model_construct(actor=ACTOR, id=ACTOR_USER_ID)

        AcceptTosHandler().handle(cmd, uow)

        updated = uow.users.get(ACTOR_USER_ID)
        assert updated.tos_accepted_at is not None

    def test_not_found_raises(self, uow):
        cmd = commands.AcceptTosCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            AcceptTosHandler().handle(cmd, uow)

    def test_other_actor_raises_unauthorized_error(self, uow):
        _make_user(uow, id=999)
        cmd = commands.AcceptTosCommand.model_construct(actor=ACTOR, id=999)

        with pytest.raises(UnauthorizedError):
            AcceptTosHandler().handle(cmd, uow)
