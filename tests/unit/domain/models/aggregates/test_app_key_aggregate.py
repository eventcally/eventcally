import pytest

from project.domain.models.aggregates.app_key_aggregate import AppKeyAggregate
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestAppKeyAggregateCreate:
    def test_creates_instance(self, actor):
        app_key = AppKeyAggregate.create(
            actor=actor,
            admin_unit_id=1,
            app_id=2,
            checksum="checksum",
            kid="kid",
            public_key="public-key",
        )
        assert app_key.id == -1
        assert app_key.admin_unit_id == 1
        assert app_key.app_id == 2
        assert app_key.checksum == "checksum"
        assert app_key.kid == "kid"
        assert app_key.public_key == "public-key"


class TestAppKeyAggregateDelete:
    def test_delete_does_not_raise(self, actor):
        app_key = AppKeyAggregate.create(
            actor=actor,
            admin_unit_id=1,
            app_id=2,
            checksum="checksum",
            kid="kid",
            public_key="public-key",
        )
        app_key.delete(actor=actor)
