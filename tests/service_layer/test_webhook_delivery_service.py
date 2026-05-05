import hashlib
import hmac
import json
import logging
from types import SimpleNamespace
from unittest.mock import Mock

import requests

from project.service_layer.services.webhook_delivery_service import (
    WebhookDeliveryService,
)


def _build_delivery(
    *,
    delivery_id=42,
    url="https://example.test/webhook",
    secret="super-secret",
    payload=None,
    event_type="event.created",
    app_installation_id=777,
):
    if payload is None:
        payload = {"id": 1, "name": "test"}

    webhook = SimpleNamespace(url=url, secret=secret)
    webhook_event = SimpleNamespace(payload=payload, event_type=event_type)

    return SimpleNamespace(
        id=delivery_id,
        webhook=webhook,
        webhook_event=webhook_event,
        app_installation_id=app_installation_id,
        attempts=[],
    )


def _build_uow_with_delivery(delivery):
    get_delivery = Mock(return_value=delivery)
    webhooks = SimpleNamespace(get_delivery=get_delivery)
    return SimpleNamespace(webhooks=webhooks), get_delivery


def test_send_webhook_delivery_sync_returns_when_delivery_missing(monkeypatch):
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))
    uow = SimpleNamespace(
        webhooks=SimpleNamespace(get_delivery=Mock(return_value=None))
    )

    post_mock = Mock()
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=123)

    assert post_mock.call_count == 0


def test_send_webhook_delivery_sync_success_adds_attempt_and_signed_headers(
    monkeypatch,
):
    payload = {"id": 10, "action": "created"}
    delivery = _build_delivery(payload=payload)
    uow, get_delivery = _build_uow_with_delivery(delivery)
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))

    response = Mock()
    response.status_code = 201
    response.raise_for_status = Mock()

    post_mock = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=delivery.id)

    assert get_delivery.call_count == 1
    post_mock.assert_called_once()

    call_kwargs = post_mock.call_args.kwargs
    data_str = json.dumps(payload)
    expected_signature = hmac.new(
        delivery.webhook.secret.encode("utf-8"),
        data_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert call_kwargs["data"] == data_str.encode("utf-8")
    assert call_kwargs["timeout"] == 10
    assert call_kwargs["headers"]["Content-Type"] == "application/json"
    assert call_kwargs["headers"]["X-EventCally-Delivery-Id"] == str(delivery.id)
    assert call_kwargs["headers"]["X-EventCally-App-Installation-Id"] == str(
        delivery.app_installation_id
    )
    assert (
        call_kwargs["headers"]["X-EventCally-Signature-256"]
        == f"sha256={expected_signature}"
    )

    assert len(delivery.attempts) == 1
    attempt = delivery.attempts[0]
    assert attempt.url == delivery.webhook.url
    assert attempt.status == "OK"
    assert attempt.status_code == "201"
    assert attempt.start_at <= attempt.end_at


def test_send_webhook_delivery_sync_timeout_adds_timeout_attempt(monkeypatch):
    delivery = _build_delivery()
    uow, _ = _build_uow_with_delivery(delivery)
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))

    post_mock = Mock(side_effect=requests.Timeout())
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=delivery.id)

    assert len(delivery.attempts) == 1
    attempt = delivery.attempts[0]
    assert attempt.status == "Timeout"
    assert attempt.status_code is None


def test_send_webhook_delivery_sync_request_exception_with_reason_is_truncated(
    monkeypatch,
):
    delivery = _build_delivery()
    uow, _ = _build_uow_with_delivery(delivery)
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))

    response = Mock()
    response.reason = "x" * 300
    post_mock = Mock(side_effect=requests.RequestException(response=response))
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=delivery.id)

    assert len(delivery.attempts) == 1
    attempt = delivery.attempts[0]
    assert attempt.status == "x" * 255
    assert attempt.status_code is None


def test_send_webhook_delivery_sync_request_exception_without_response_uses_type(
    monkeypatch,
):
    delivery = _build_delivery(secret=None, app_installation_id=None)
    uow, _ = _build_uow_with_delivery(delivery)
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))

    post_mock = Mock(side_effect=requests.RequestException())
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=delivery.id)

    assert len(delivery.attempts) == 1
    attempt = delivery.attempts[0]
    assert attempt.status == "RequestException"
    assert attempt.status_code is None

    call_headers = post_mock.call_args.kwargs["headers"]
    assert "X-EventCally-Signature-256" not in call_headers
    assert "X-EventCally-App-Installation-Id" not in call_headers


def test_send_webhook_delivery_sync_request_exception_with_utf8_bytes_reason(
    monkeypatch,
):
    delivery = _build_delivery()
    uow, _ = _build_uow_with_delivery(delivery)
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))

    response = Mock()
    response.reason = "Über den Wolken".encode("utf-8")
    post_mock = Mock(side_effect=requests.RequestException(response=response))
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=delivery.id)

    assert len(delivery.attempts) == 1
    attempt = delivery.attempts[0]
    assert attempt.status == "Über den Wolken"
    assert attempt.status_code is None


def test_send_webhook_delivery_sync_request_exception_with_non_utf8_bytes_reason(
    monkeypatch,
):
    delivery = _build_delivery()
    uow, _ = _build_uow_with_delivery(delivery)
    service = WebhookDeliveryService(logger=logging.getLogger(__name__))

    response = Mock()
    response.reason = b"\xff"
    post_mock = Mock(side_effect=requests.RequestException(response=response))
    monkeypatch.setattr(requests, "post", post_mock)

    service.send_webhook_delivery_sync(uow, webhook_delivery_id=delivery.id)

    assert len(delivery.attempts) == 1
    attempt = delivery.attempts[0]
    assert attempt.status == "ÿ"
    assert attempt.status_code is None
