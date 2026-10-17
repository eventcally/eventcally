"""OAuth2 token query handlers and read model — no database."""

import time

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetUserOAuth2TokenHandler,
    ListUserOAuth2TokensHandler,
)
from project.application.read_models.oauth2_token_read_models import (
    OAuth2TokenReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_oauth2_token_read_repository import (
    AbstractOAuth2TokenReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.application.query_handlers.authz_helpers import ACTOR, authz


def _token(token_id, user_id=7, **kwargs):
    return OAuth2TokenReadModel(
        id=token_id, user_id=user_id, issued_at=int(time.time()), **kwargs
    )


class FakeRepo(AbstractOAuth2TokenReadRepository):
    def __init__(self, tokens=()):
        self.tokens = {t.id: t for t in tokens}

    def list(self, query):
        items = list(self.tokens.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get(self, object_id):
        return self.tokens.get(object_id)


def test_read_model_mirrors_authlib_checks():
    assert not _token(1, expires_in=3600).is_expired()
    assert OAuth2TokenReadModel(id=1, issued_at=0, expires_in=10).is_expired()
    assert not OAuth2TokenReadModel(id=1, issued_at=0).is_expired()
    assert not _token(1).is_revoked()
    assert _token(1, access_token_revoked_at=5).is_revoked() == 5
    token = OAuth2TokenReadModel(id=1, issued_at=0, expires_in=60)
    assert token.issued_at_datetime.timestamp() == 0
    assert token.expires_at_datetime.timestamp() == 60


def test_handlers():
    repo = FakeRepo([_token(1), _token(2, user_id=8)])

    assert (
        ListUserOAuth2TokensHandler(repo, authz())
        .handle(queries.ListUserOAuth2TokensQuery(user_id=7, actor=ACTOR))
        .total
        == 2
    )
    with pytest.raises(UnauthorizedError):
        ListUserOAuth2TokensHandler(repo, authz()).handle(
            queries.ListUserOAuth2TokensQuery(user_id=8, actor=ACTOR)
        )

    handler = GetUserOAuth2TokenHandler(repo, authz())
    assert handler.handle(queries.GetUserOAuth2TokenQuery(id=1, actor=ACTOR)).id == 1
    assert handler.handle(queries.GetUserOAuth2TokenQuery(id=3, actor=ACTOR)) is None
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.GetUserOAuth2TokenQuery(id=2, actor=ACTOR))
