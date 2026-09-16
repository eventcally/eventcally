"""Unit tests for OAuth2Token command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.revoke_oauth2_token_handler import (
    RevokeOAuth2TokenHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.oauth2_token_aggregate import OAuth2TokenAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID

OTHER_USER_ID = 2


def _seed_token(uow, user_id=ACTOR_USER_ID, is_revoked=False):
    token = OAuth2TokenAggregate(id=-1, user_id=user_id, is_revoked=is_revoked)
    uow.oauth2_tokens.add(token)
    return token


class TestRevokeOAuth2TokenHandler:
    def test_revokes_own_token(self, uow):
        token = _seed_token(uow, user_id=ACTOR_USER_ID)
        cmd = commands.RevokeOAuth2TokenCommand.model_construct(
            actor=ACTOR, id=token.id
        )

        RevokeOAuth2TokenHandler().handle(cmd, uow)

        assert uow.oauth2_tokens.get(token.id).is_revoked is True

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.RevokeOAuth2TokenCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            RevokeOAuth2TokenHandler().handle(cmd, uow)

    def test_other_users_token_raises_unauthorized_error(self, uow):
        token = _seed_token(uow, user_id=OTHER_USER_ID)
        cmd = commands.RevokeOAuth2TokenCommand.model_construct(
            actor=ACTOR, id=token.id
        )

        with pytest.raises(UnauthorizedError):
            RevokeOAuth2TokenHandler().handle(cmd, uow)

    def test_already_revoked_raises_constraint_error(self, uow):
        token = _seed_token(uow, user_id=ACTOR_USER_ID, is_revoked=True)
        cmd = commands.RevokeOAuth2TokenCommand.model_construct(
            actor=ACTOR, id=token.id
        )

        with pytest.raises(ConstraintError):
            RevokeOAuth2TokenHandler().handle(cmd, uow)
