import pytest

from project.domain.events.app_deleted import AppDeleted
from project.domain.events.app_updated import AppUpdated
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor


class _ConcreteAggregate(BaseAggregate):
    id: int = 0


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestBaseAggregateHash:
    def test_different_instances_have_different_hash(self):
        a = _ConcreteAggregate()
        b = _ConcreteAggregate()
        assert hash(a) != hash(b)

    def test_same_instance_has_same_hash(self):
        a = _ConcreteAggregate()
        assert hash(a) == hash(a)

    def test_instances_not_equal_by_default(self):
        a = _ConcreteAggregate()
        b = _ConcreteAggregate()
        assert a is not b


class TestGetFirstDomainEventByType:
    def test_returns_matching_event(self, actor):
        agg = _ConcreteAggregate()
        ev1 = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        ev2 = AppUpdated(actor=actor, id=1, admin_unit_id=2)
        agg.domain_events = [ev1, ev2]
        result = agg.get_first_domain_event_by_type(AppDeleted)
        assert result is ev1

    def test_returns_first_of_multiple_matching(self, actor):
        agg = _ConcreteAggregate()
        ev1 = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        ev2 = AppDeleted(actor=actor, id=3, admin_unit_id=4)
        agg.domain_events = [ev1, ev2]
        result = agg.get_first_domain_event_by_type(AppDeleted)
        assert result is ev1

    def test_domain_events_default_empty(self):
        agg = _ConcreteAggregate()
        assert agg.domain_events == []
