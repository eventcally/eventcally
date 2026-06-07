import datetime

import pytest

from project.domain.events.webhook_delivery_created import WebhookDeliveryCreated
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)
from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)
from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def now():
    return datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)


class TestWebhookDeliveryAggregate:
    def test_create_returns_instance(self, actor):
        delivery = WebhookDeliveryAggregate.create(
            actor=actor, webhook_event_id=10, webhook_id=20
        )
        assert delivery.webhook_event_id == 10
        assert delivery.webhook_id == 20

    def test_create_appends_delivery_created_event(self, actor):
        delivery = WebhookDeliveryAggregate.create(
            actor=actor, webhook_event_id=10, webhook_id=20
        )
        assert len(delivery.domain_events) == 1
        assert isinstance(delivery.domain_events[0], WebhookDeliveryCreated)

    def test_optional_fields_default_none(self, actor):
        delivery = WebhookDeliveryAggregate.create(
            actor=actor, webhook_event_id=1, webhook_id=2
        )
        assert delivery.app_installation_id is None
        assert delivery.app_id is None

    def test_create_with_optional_ids(self, actor):
        delivery = WebhookDeliveryAggregate.create(
            actor=actor,
            webhook_event_id=1,
            webhook_id=2,
            app_installation_id=3,
            app_id=4,
        )
        assert delivery.app_installation_id == 3
        assert delivery.app_id == 4


class TestWebhookDeliveryAttemptAggregate:
    def test_create_returns_instance(self, actor, now):
        end = now + datetime.timedelta(seconds=5)
        attempt = WebhookDeliveryAttemptAggregate.create(
            actor=actor,
            url="https://example.com/hook",
            start_at=now,
            end_at=end,
            webhook_delivery_id=99,
        )
        assert attempt.url == "https://example.com/hook"
        assert attempt.webhook_delivery_id == 99
        assert attempt.start_at == now
        assert attempt.end_at == end

    def test_no_domain_events_appended(self, actor, now):
        end = now + datetime.timedelta(seconds=1)
        attempt = WebhookDeliveryAttemptAggregate.create(
            actor=actor,
            url="https://example.com",
            start_at=now,
            end_at=end,
            webhook_delivery_id=1,
        )
        assert len(attempt.domain_events) == 0

    def test_optional_status_defaults_none(self, actor, now):
        end = now + datetime.timedelta(seconds=1)
        attempt = WebhookDeliveryAttemptAggregate.create(
            actor=actor,
            url="https://example.com",
            start_at=now,
            end_at=end,
            webhook_delivery_id=1,
        )
        assert attempt.status is None
        assert attempt.status_code is None

    def test_create_with_status(self, actor, now):
        end = now + datetime.timedelta(seconds=1)
        attempt = WebhookDeliveryAttemptAggregate.create(
            actor=actor,
            url="https://example.com",
            start_at=now,
            end_at=end,
            webhook_delivery_id=1,
            status="ok",
            status_code="200",
        )
        assert attempt.status == "ok"
        assert attempt.status_code == "200"


class TestWebhookEventAggregate:
    def test_create_returns_instance(self, actor, now):
        agg = WebhookEventAggregate.create(
            actor=actor,
            timestamp=now,
            event_type="event.created",
            payload={"key": "value"},
        )
        assert agg.event_type == "event.created"
        assert agg.payload == {"key": "value"}
        assert agg.timestamp == now

    def test_no_domain_events_appended(self, actor, now):
        agg = WebhookEventAggregate.create(
            actor=actor,
            timestamp=now,
            event_type="event.deleted",
            payload={},
        )
        assert len(agg.domain_events) == 0


class TestEventReferenceAggregate:
    def test_instantiation(self):
        ref = EventReferenceAggregate(id=1, admin_unit_id=2, event_id=3)
        assert ref.id == 1
        assert ref.admin_unit_id == 2
        assert ref.event_id == 3


class TestOrganisationMemberAggregate:
    def test_instantiation(self):
        member = OrganisationMemberAggregate(id=1, admin_unit_id=2, user_id=3)
        assert member.id == 1
        assert member.user_id == 3
