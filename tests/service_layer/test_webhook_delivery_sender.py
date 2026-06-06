import hashlib
import hmac
import json
import logging
from unittest.mock import Mock

import requests

from project.infrastructure.services.requests_webhook_delivery_sender import (
    RequestsWebhookDeliverySender,
)


def _make_sender():
    return RequestsWebhookDeliverySender(logger=logging.getLogger(__name__))


def test_send_success_builds_headers_and_signature(monkeypatch):
    sender = _make_sender()
    payload = {"id": 10, "action": "created"}

    response = Mock()
    response.status_code = 201
    response.raise_for_status = Mock()
    post_mock = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret="super-secret",
        payload=payload,
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=777,
    )

    assert status == "OK"
    assert status_code == "201"

    call_kwargs = post_mock.call_args.kwargs
    data_str = json.dumps(payload)
    expected_signature = hmac.new(
        b"super-secret", data_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    assert call_kwargs["data"] == data_str.encode("utf-8")
    assert call_kwargs["timeout"] == 10
    assert call_kwargs["headers"]["Content-Type"] == "application/json"
    assert call_kwargs["headers"]["X-EventCally-Delivery-Id"] == "42"
    assert call_kwargs["headers"]["X-EventCally-Event"] == "event.created"
    assert call_kwargs["headers"]["X-EventCally-App-Installation-Id"] == "777"
    assert call_kwargs["headers"]["X-EventCally-Signature-256"] == (
        f"sha256={expected_signature}"
    )


def test_send_without_secret_or_installation_headers(monkeypatch):
    sender = _make_sender()

    response = Mock()
    response.status_code = 200
    response.raise_for_status = Mock()
    post_mock = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret=None,
        payload={"x": 1},
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=None,
    )

    assert status == "OK"
    assert status_code == "200"

    headers = post_mock.call_args.kwargs["headers"]
    assert "X-EventCally-Signature-256" not in headers
    assert "X-EventCally-App-Installation-Id" not in headers


def test_send_timeout(monkeypatch):
    sender = _make_sender()

    post_mock = Mock(side_effect=requests.Timeout())
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret=None,
        payload={"x": 1},
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=None,
    )

    assert status == "Timeout"
    assert status_code is None


def test_send_request_exception_reason_truncated(monkeypatch):
    sender = _make_sender()

    response = Mock()
    response.reason = "x" * 300
    post_mock = Mock(side_effect=requests.RequestException(response=response))
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret=None,
        payload={"x": 1},
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=None,
    )

    assert status == "x" * 255
    assert status_code is None


def test_send_request_exception_without_response_uses_type(monkeypatch):
    sender = _make_sender()

    post_mock = Mock(side_effect=requests.RequestException())
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret=None,
        payload={"x": 1},
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=None,
    )

    assert status == "RequestException"
    assert status_code is None


def test_send_request_exception_with_utf8_bytes_reason(monkeypatch):
    sender = _make_sender()

    response = Mock()
    response.reason = "Über den Wolken".encode("utf-8")
    post_mock = Mock(side_effect=requests.RequestException(response=response))
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret=None,
        payload={"x": 1},
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=None,
    )

    assert status == "Über den Wolken"
    assert status_code is None


def test_send_request_exception_with_non_utf8_bytes_reason(monkeypatch):
    sender = _make_sender()

    response = Mock()
    response.reason = b"\xff"
    post_mock = Mock(side_effect=requests.RequestException(response=response))
    monkeypatch.setattr(requests, "post", post_mock)

    status, status_code = sender.send(
        url="https://example.test/webhook",
        secret=None,
        payload={"x": 1},
        event_type="event.created",
        webhook_delivery_id=42,
        app_installation_id=None,
    )

    assert status == "ÿ"
    assert status_code is None
