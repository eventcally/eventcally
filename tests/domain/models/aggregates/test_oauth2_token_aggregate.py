import pytest

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.oauth2_token_aggregate import OAuth2TokenAggregate
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestOAuth2TokenAggregateRevoke:
    def test_revoke_sets_is_revoked(self, actor):
        token = OAuth2TokenAggregate(id=1, user_id=1, is_revoked=False)
        token.revoke(actor=actor)
        assert token.is_revoked is True

    def test_revoke_already_revoked_raises_constraint_error(self, actor):
        token = OAuth2TokenAggregate(id=1, user_id=1, is_revoked=True)
        with pytest.raises(ConstraintError):
            token.revoke(actor=actor)
