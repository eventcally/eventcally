"""Unit tests for micro-gap coverage in service layer / domain / infrastructure."""

from unittest.mock import Mock

from project.domain.repositories.abstract_webhook_repository import (
    AbstractWebhookRepository,
)
from project.domain.types import unset
from project.infrastructure.repositories.sql_alchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)
from project.service_layer.webhooks.app_installation_webhooks import (
    get_app_installation_webhook_info_by_event_type,
)
from project.service_layer.webhooks.app_webhooks import (
    get_app_webhook_info_by_event_type,
)
from project.service_layer.webhooks.payloads.nested.actor import Actor as ActorPayload
from project.service_layer.webhooks.payloads.nested.image_created import (
    ImageCreated as ImageCreatedPayload,
)
from project.service_layer.webhooks.payloads.nested.image_updated import (
    ImageUpdated as ImageUpdatedPayload,
)
from project.service_layer.webhooks.payloads.nested.location_created import (
    LocationCreated as LocationCreatedPayload,
)
from project.service_layer.webhooks.payloads.nested.location_updated import (
    LocationUpdated as LocationUpdatedPayload,
)
from project.service_layer.webhooks.schema_exporter import export_all_webhook_schemas

# ---------------------------------------------------------------------------
# abstract_webhook_repository – get_delivery / get_delivery_attempt with results
# ---------------------------------------------------------------------------


class _ConcreteWebhookRepo(AbstractWebhookRepository):
    """Minimal concrete implementation for testing base-class logic."""

    def __init__(self, delivery=None, attempt=None):
        super().__init__()
        self._delivery = delivery
        self._attempt = attempt

    def _add_event(self, event):
        pass

    def _get_delivery(self, object_id):
        return self._delivery

    def _get_delivery_attempt(self, object_id):
        return self._attempt

    def _delete_old_events(self, days):
        return 0


def test_abstract_webhook_repo_get_delivery_with_result():
    delivery = object()
    repo = _ConcreteWebhookRepo(delivery=delivery)
    result = repo.get_delivery(1)
    assert result is delivery
    assert delivery in repo.seen


def test_abstract_webhook_repo_get_delivery_without_result():
    repo = _ConcreteWebhookRepo(delivery=None)
    result = repo.get_delivery(1)
    assert result is None
    assert len(repo.seen) == 0


def test_abstract_webhook_repo_get_delivery_attempt_with_result():
    attempt = object()
    repo = _ConcreteWebhookRepo(attempt=attempt)
    result = repo.get_delivery_attempt(1)
    assert result is attempt
    assert attempt in repo.seen


def test_abstract_webhook_repo_get_delivery_attempt_without_result():
    repo = _ConcreteWebhookRepo(attempt=None)
    result = repo.get_delivery_attempt(1)
    assert result is None
    assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# sql_alchemy_webhook_repository – _get_delivery / _get_delivery_attempt
# ---------------------------------------------------------------------------


def test_sqla_webhook_repo_get_delivery():
    session = Mock()
    session.query.return_value.filter_by.return_value.first.return_value = "delivery"
    repo = SqlAlchemyWebhookRepository(session=session)
    result = repo._get_delivery(42)
    assert result == "delivery"


def test_sqla_webhook_repo_get_delivery_attempt():
    session = Mock()
    session.query.return_value.filter_by.return_value.first.return_value = "attempt"
    repo = SqlAlchemyWebhookRepository(session=session)
    result = repo._get_delivery_attempt(77)
    assert result == "attempt"


# ---------------------------------------------------------------------------
# app_webhooks – get_app_webhook_info_by_event_type returns None for unknown
# ---------------------------------------------------------------------------


def test_get_app_webhook_info_returns_none_for_unknown_event_type():
    result = get_app_webhook_info_by_event_type("unknown.event")
    assert result is None


# ---------------------------------------------------------------------------
# app_installation_webhooks – returns None for unknown event type
# ---------------------------------------------------------------------------


def test_get_app_installation_webhook_info_returns_none_for_unknown_event_type():
    result = get_app_installation_webhook_info_by_event_type("unknown.event")
    assert result is None


# ---------------------------------------------------------------------------
# schema_exporter – export_all_webhook_schemas
# ---------------------------------------------------------------------------


def test_export_all_webhook_schemas_returns_dict():
    result = export_all_webhook_schemas()
    assert isinstance(result, dict)
    assert "$defs" in result or "title" in result


# ---------------------------------------------------------------------------
# nested payload – actor None branch
# ---------------------------------------------------------------------------


def test_actor_payload_from_event_none_returns_none():
    ctx = Mock()
    result = ActorPayload.from_event(None, ctx)
    assert result is None


# ---------------------------------------------------------------------------
# nested payload – image_created None branch
# ---------------------------------------------------------------------------


def test_image_created_payload_from_event_none_returns_none():
    ctx = Mock()
    result = ImageCreatedPayload.from_event(None, ctx)
    assert result is None


# ---------------------------------------------------------------------------
# nested payload – image_updated unset and None branches
# ---------------------------------------------------------------------------


def test_image_updated_payload_from_event_unset_returns_unset():
    ctx = Mock()
    result = ImageUpdatedPayload.from_event(unset, ctx)
    assert result is unset


def test_image_updated_payload_from_event_none_returns_none():
    ctx = Mock()
    result = ImageUpdatedPayload.from_event(None, ctx)
    assert result is None


# ---------------------------------------------------------------------------
# nested payload – location_created None branch
# ---------------------------------------------------------------------------


def test_location_created_payload_from_event_none_returns_none():
    ctx = Mock()
    result = LocationCreatedPayload.from_event(None, ctx)
    assert result is None


# ---------------------------------------------------------------------------
# nested payload – location_updated unset and None branches
# ---------------------------------------------------------------------------


def test_location_updated_payload_from_event_unset_returns_unset():
    ctx = Mock()
    result = LocationUpdatedPayload.from_event(unset, ctx)
    assert result is unset


def test_location_updated_payload_from_event_none_returns_none():
    ctx = Mock()
    result = LocationUpdatedPayload.from_event(None, ctx)
    assert result is None
