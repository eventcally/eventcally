import pytest

from project.application import queries
from project.application.query_handlers import GetUserProfileHandler
from project.application.read_models.user_profile_read_model import UserProfileReadModel
from project.application.read_repositories.abstract_user_profile_read_repository import (
    AbstractUserProfileReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader


class FakeRepo(AbstractUserProfileReadRepository):
    def get_profile(self, user_id):
        if user_id != 1:
            return None
        return UserProfileReadModel(id=1, email="a@test.de", locale="de")


def _handle(query):
    return GetUserProfileHandler(
        FakeRepo(), ActorAuthorizationService(FakeReader())
    ).handle(query)


def test_a_user_reads_their_own_profile():
    profile = _handle(queries.GetUserProfileQuery(user_id=1, actor=Actor(user_id=1)))
    assert profile.email == "a@test.de"
    assert profile.locale == "de"


def test_a_missing_user_is_none():
    assert (
        _handle(queries.GetUserProfileQuery(user_id=2, actor=Actor(user_id=2))) is None
    )


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
def test_everyone_else_is_refused(actor):
    with pytest.raises(UnauthorizedError):
        _handle(queries.GetUserProfileQuery(user_id=1, actor=actor))
