import pytest

from project.domain.events.user_deletion_cancelled import UserDeletionCancelled
from project.domain.events.user_deletion_requested import UserDeletionRequested
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def user():
    return UserAggregate(id=10, email="test@test.de", locale=None)


class TestUserAggregateRequestDeletion:
    def test_sets_deletion_requested_at(self, user, actor):
        user.request_deletion(actor)
        assert user.deletion_requested_at is not None

    def test_appends_deletion_requested_event(self, user, actor):
        user.request_deletion(actor)
        assert len(user.domain_events) == 1
        event = user.domain_events[0]
        assert isinstance(event, UserDeletionRequested)

    def test_event_has_correct_id(self, user, actor):
        user.request_deletion(actor)
        event = user.domain_events[0]
        assert event.id == user.id

    def test_event_has_correct_actor(self, user, actor):
        user.request_deletion(actor)
        event = user.domain_events[0]
        assert event.actor == actor


class TestUserAggregateCancelDeletion:
    def test_clears_deletion_requested_at(self, user, actor):
        user.request_deletion(actor)
        user.cancel_deletion(actor)
        assert user.deletion_requested_at is None

    def test_appends_deletion_cancelled_event(self, user, actor):
        user.cancel_deletion(actor)
        assert len(user.domain_events) == 1
        event = user.domain_events[0]
        assert isinstance(event, UserDeletionCancelled)

    def test_event_has_correct_id(self, user, actor):
        user.cancel_deletion(actor)
        event = user.domain_events[0]
        assert event.id == user.id


class TestUserAggregateAcceptTos:
    def test_sets_tos_accepted_at(self, user, actor):
        user.accept_tos(actor)
        assert user.tos_accepted_at is not None


class TestUserAggregateUpdate:
    def test_updates_locale(self, user, actor):
        user.update(actor=actor, locale="de")
        assert user.locale == "de"

    def test_updates_locale_to_none(self, user, actor):
        user.update(actor=actor, locale="de")
        user.update(actor=actor, locale=None)
        assert user.locale is None

    def test_updates_newsletter_enabled(self, user, actor):
        user.update(actor=actor, newsletter_enabled=False)
        assert user.newsletter_enabled is False

    def test_updates_roles(self, user, actor):
        user.update(actor=actor, roles=["admin"])
        assert user.roles == ["admin"]

    def test_leaves_omitted_fields_untouched(self, user, actor):
        user.update(actor=actor, locale="de", newsletter_enabled=False, roles=["admin"])
        user.update(actor=actor)

        assert user.locale == "de"
        assert user.newsletter_enabled is False
        assert user.roles == ["admin"]


class TestUserAggregateDelete:
    def test_delete_does_not_raise(self, user, actor):
        user.delete(actor=actor)
