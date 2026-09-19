import pytest

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestApiKeyAggregateCreate:
    def test_creates_instance_with_user_owner(self, actor):
        api_key = ApiKeyAggregate.create(
            actor=actor, name="My Key", key_hash="hash", user_id=1
        )
        assert api_key.id == -1
        assert api_key.name == "My Key"
        assert api_key.key_hash == "hash"
        assert api_key.user_id == 1
        assert api_key.admin_unit_id is None

    def test_creates_instance_with_admin_unit_owner(self, actor):
        api_key = ApiKeyAggregate.create(
            actor=actor, name="Org Key", key_hash="hash", admin_unit_id=2
        )
        assert api_key.user_id is None
        assert api_key.admin_unit_id == 2

    def test_both_owners_set_raises_constraint_error(self, actor):
        with pytest.raises(ConstraintError):
            ApiKeyAggregate.create(
                actor=actor,
                name="Key",
                key_hash="hash",
                user_id=1,
                admin_unit_id=2,
            )

    def test_no_owner_set_raises_constraint_error(self, actor):
        with pytest.raises(ConstraintError):
            ApiKeyAggregate.create(actor=actor, name="Key", key_hash="hash")


class TestApiKeyAggregateUpdate:
    def test_update_changes_name(self, actor):
        api_key = ApiKeyAggregate.create(
            actor=actor, name="Old Name", key_hash="hash", user_id=1
        )
        api_key.update(actor=actor, name="New Name")
        assert api_key.name == "New Name"

    def test_update_with_no_changes_leaves_name_untouched(self, actor):
        api_key = ApiKeyAggregate.create(
            actor=actor, name="Name", key_hash="hash", user_id=1
        )
        api_key.update(actor=actor)
        assert api_key.name == "Name"


class TestApiKeyAggregateDelete:
    def test_delete_does_not_raise(self, actor):
        api_key = ApiKeyAggregate.create(
            actor=actor, name="Name", key_hash="hash", user_id=1
        )
        api_key.delete(actor=actor)
