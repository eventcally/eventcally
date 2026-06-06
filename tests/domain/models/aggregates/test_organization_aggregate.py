import pytest

from project.domain.events.organization_deletion_cancelled import (
    OrganizationDeletionCancelled,
)
from project.domain.events.organization_deletion_requested import (
    OrganizationDeletionRequested,
)
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def org():
    return OrganizationAggregate(id=10)


class TestOrganizationAggregateRequestDeletion:
    def test_sets_deletion_requested_at(self, org, actor):
        org.request_deletion(actor)
        assert org.deletion_requested_at is not None

    def test_sets_deletion_requested_by_id(self, org, actor):
        org.request_deletion(actor)
        assert org.deletion_requested_by_id == actor.user_id

    def test_appends_deletion_requested_event(self, org, actor):
        org.request_deletion(actor)
        assert len(org.domain_events) == 1
        event = org.domain_events[0]
        assert isinstance(event, OrganizationDeletionRequested)

    def test_event_has_correct_id(self, org, actor):
        org.request_deletion(actor)
        event = org.domain_events[0]
        assert event.id == org.id

    def test_event_has_correct_actor(self, org, actor):
        org.request_deletion(actor)
        event = org.domain_events[0]
        assert event.actor == actor


class TestOrganizationAggregateCancelDeletion:
    def test_clears_deletion_requested_at(self, org, actor):
        org.request_deletion(actor)
        org.cancel_deletion(actor)
        assert org.deletion_requested_at is None

    def test_clears_deletion_requested_by_id(self, org, actor):
        org.request_deletion(actor)
        org.cancel_deletion(actor)
        assert org.deletion_requested_by_id is None

    def test_appends_deletion_cancelled_event(self, org, actor):
        org.cancel_deletion(actor)
        assert len(org.domain_events) == 1
        event = org.domain_events[0]
        assert isinstance(event, OrganizationDeletionCancelled)

    def test_event_has_correct_id(self, org, actor):
        org.cancel_deletion(actor)
        event = org.domain_events[0]
        assert event.id == org.id


class TestOrganizationAggregateDefaults:
    def test_deletion_requested_at_defaults_none(self):
        org = OrganizationAggregate(id=1)
        assert org.deletion_requested_at is None

    def test_deletion_requested_by_id_defaults_none(self):
        org = OrganizationAggregate(id=1)
        assert org.deletion_requested_by_id is None
