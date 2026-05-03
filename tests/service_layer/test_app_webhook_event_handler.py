import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from project.domain import events
from project.domain.types.actor import Actor
from project.service_layer.event_handlers import app_webhook_event_handler


class _FakeWebhookEvent:
    def __init__(self, event_type, timestamp, payload):
        self.event_type = event_type
        self.timestamp = timestamp
        self.payload = payload
        self.deliveries = []


class _FakeWebhookDelivery:
    _next_id = 200

    def __init__(self, app_id, webhook_id):
        self.app_id = app_id
        self.webhook_id = webhook_id
        self.id = _FakeWebhookDelivery._next_id
        _FakeWebhookDelivery._next_id += 1


def _make_event(app_id=42):
    return events.AppInstallationCreated(
        actor=Actor(),
        id=1,
        admin_unit_id=10,
        app_id=app_id,
        permissions=[],
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


class _FakeUow:
    def __init__(self, app=None):
        self.apps = SimpleNamespace(get=Mock(return_value=app))
        self.webhooks = SimpleNamespace(add_event=Mock())
        self.pending_events = []
        self.commit = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def _make_uow(app=None):
    return _FakeUow(app=app)


def _fake_webhook_info(event_type="app.installed"):
    payload_obj = SimpleNamespace(model_dump=Mock(return_value={"ok": True}))
    payload_cls = SimpleNamespace(from_event=Mock(return_value=payload_obj))
    return SimpleNamespace(
        event_type=event_type,
        payload_cls=payload_cls,
    )


def test_handle_returns_early_when_app_missing(monkeypatch):
    handler = app_webhook_event_handler.AppWebhookEventHandler()
    event = _make_event(app_id=99)
    uow = _make_uow(app=None)
    info = _fake_webhook_info()

    monkeypatch.setattr(
        app_webhook_event_handler,
        "get_app_webhook_info_by_event_type",
        Mock(return_value=info),
    )

    handler.handle(event, uow)

    assert uow.webhooks.add_event.call_count == 0
    assert uow.commit.call_count == 0
    assert uow.pending_events == []


def test_handle_returns_early_when_no_webhook(monkeypatch):
    handler = app_webhook_event_handler.AppWebhookEventHandler()
    event = _make_event()
    app = SimpleNamespace(id=42, webhook=None)
    uow = _make_uow(app=app)
    info = _fake_webhook_info()

    monkeypatch.setattr(
        app_webhook_event_handler,
        "get_app_webhook_info_by_event_type",
        Mock(return_value=info),
    )

    handler.handle(event, uow)

    assert uow.webhooks.add_event.call_count == 0
    assert uow.commit.call_count == 0
    assert uow.pending_events == []


def test_handle_returns_early_when_event_type_not_enabled(monkeypatch):
    handler = app_webhook_event_handler.AppWebhookEventHandler()
    event = _make_event()
    webhook = SimpleNamespace(
        id=7001,
        is_enabled_for_event_type=Mock(return_value=False),
    )
    app = SimpleNamespace(id=42, webhook=webhook)
    uow = _make_uow(app=app)
    info = _fake_webhook_info()

    monkeypatch.setattr(
        app_webhook_event_handler,
        "get_app_webhook_info_by_event_type",
        Mock(return_value=info),
    )

    handler.handle(event, uow)

    assert uow.webhooks.add_event.call_count == 0
    assert uow.commit.call_count == 0
    assert uow.pending_events == []


def test_handle_creates_webhook_event_delivery_and_pending_event(monkeypatch):
    handler = app_webhook_event_handler.AppWebhookEventHandler()
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    event = events.AppInstallationCreated(
        actor=Actor(),
        id=1,
        admin_unit_id=10,
        app_id=42,
        permissions=[],
        timestamp=timestamp,
    )
    webhook = SimpleNamespace(
        id=7001,
        is_enabled_for_event_type=Mock(return_value=True),
    )
    app = SimpleNamespace(id=42, webhook=webhook)
    uow = _make_uow(app=app)
    info = _fake_webhook_info("app.installed")

    monkeypatch.setattr(
        app_webhook_event_handler,
        "get_app_webhook_info_by_event_type",
        Mock(return_value=info),
    )
    monkeypatch.setattr(
        app_webhook_event_handler,
        "WebhookEvent",
        _FakeWebhookEvent,
    )
    monkeypatch.setattr(
        app_webhook_event_handler,
        "WebhookDelivery",
        _FakeWebhookDelivery,
    )

    handler.handle(event, uow)

    uow.apps.get.assert_called_once_with(42)
    info.payload_cls.from_event.assert_called_once()

    added_event = uow.webhooks.add_event.call_args.args[0]
    assert added_event.event_type == "app.installed"
    assert added_event.timestamp == timestamp
    assert added_event.payload == {"ok": True}
    assert len(added_event.deliveries) == 1

    delivery = added_event.deliveries[0]
    assert delivery.app_id == 42
    assert delivery.webhook_id == 7001

    uow.commit.assert_called_once()
    assert len(uow.pending_events) == 1
    pending = uow.pending_events[0]
    assert isinstance(pending, events.WebhookDeliveryCreated)
    assert pending.id == delivery.id
