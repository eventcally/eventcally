import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from project.domain import events
from project.domain.types.actor import Actor
from project.service_layer.event_handlers import app_installation_webhook_event_handler


class _FakeWebhookEvent:
    def __init__(self, event_type, timestamp, payload):
        self.event_type = event_type
        self.timestamp = timestamp
        self.payload = payload
        self.deliveries = []


class _FakeWebhookDelivery:
    _next_id = 100

    def __init__(self, app_id, app_installation_id, webhook_id):
        self.app_id = app_id
        self.app_installation_id = app_installation_id
        self.webhook_id = webhook_id
        self.id = _FakeWebhookDelivery._next_id
        _FakeWebhookDelivery._next_id += 1


class _FakeUow:
    def __init__(self, installations):
        self.installations = installations
        self.organizations = SimpleNamespace(
            get_app_installations_with_webhook=Mock(return_value=installations)
        )
        self.webhooks = SimpleNamespace(add_event=Mock())
        self.pending_events = []
        self.commit = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def _fake_webhook_info(event_type="event_organizer.created"):
    payload_obj = SimpleNamespace(model_dump=Mock(return_value={"ok": True}))
    payload_cls = SimpleNamespace(from_event=Mock(return_value=payload_obj))
    return SimpleNamespace(
        permissions=["event_organizers:read"],
        event_type=event_type,
        payload_cls=payload_cls,
    )


def test_handle_returns_early_when_no_installations(monkeypatch):
    handler = (
        app_installation_webhook_event_handler.AppInstallationWebhookEventHandler()
    )
    event = events.EventOrganizerCreated(
        actor=Actor(),
        id=1,
        admin_unit_id=5,
        name="Organizer",
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    uow = _FakeUow(installations=[])
    info = _fake_webhook_info("event_organizer.created")

    monkeypatch.setattr(
        app_installation_webhook_event_handler,
        "get_app_installation_webhook_info_by_event_type",
        Mock(return_value=info),
    )

    handler.handle(event, uow)

    uow.organizations.get_app_installations_with_webhook.assert_called_once_with(
        5,
        info.permissions,
        info.event_type,
    )
    assert uow.webhooks.add_event.call_count == 0
    assert uow.commit.call_count == 0
    assert uow.pending_events == []


def test_handle_creates_webhook_event_deliveries_and_pending_events(monkeypatch):
    handler = (
        app_installation_webhook_event_handler.AppInstallationWebhookEventHandler()
    )
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    event = events.EventOrganizerCreated(
        actor=Actor(),
        id=2,
        admin_unit_id=11,
        name="Second Organizer",
        timestamp=timestamp,
    )
    installations = [
        SimpleNamespace(
            id=900,
            oauth2_client_id=301,
            oauth2_client=SimpleNamespace(webhook_id=7001),
        ),
        SimpleNamespace(
            id=901,
            oauth2_client_id=302,
            oauth2_client=SimpleNamespace(webhook_id=7002),
        ),
    ]
    uow = _FakeUow(installations=installations)
    info = _fake_webhook_info("event_organizer.created")

    monkeypatch.setattr(
        app_installation_webhook_event_handler,
        "get_app_installation_webhook_info_by_event_type",
        Mock(return_value=info),
    )
    monkeypatch.setattr(
        app_installation_webhook_event_handler,
        "WebhookEvent",
        _FakeWebhookEvent,
    )
    monkeypatch.setattr(
        app_installation_webhook_event_handler,
        "WebhookDelivery",
        _FakeWebhookDelivery,
    )

    handler.handle(event, uow)

    uow.organizations.get_app_installations_with_webhook.assert_called_once_with(
        11,
        info.permissions,
        info.event_type,
    )
    info.payload_cls.from_event.assert_called_once()

    added_event = uow.webhooks.add_event.call_args.args[0]
    assert added_event.event_type == info.event_type
    assert added_event.timestamp == timestamp
    assert added_event.payload == {"ok": True}
    assert len(added_event.deliveries) == 2

    first_delivery = added_event.deliveries[0]
    second_delivery = added_event.deliveries[1]
    assert first_delivery.app_id == 301
    assert first_delivery.app_installation_id == 900
    assert first_delivery.webhook_id == 7001
    assert second_delivery.app_id == 302
    assert second_delivery.app_installation_id == 901
    assert second_delivery.webhook_id == 7002

    assert uow.commit.call_count == 1
    assert len(uow.pending_events) == 2
    assert isinstance(uow.pending_events[0], events.WebhookDeliveryCreated)
    assert isinstance(uow.pending_events[1], events.WebhookDeliveryCreated)
    assert uow.pending_events[0].id == first_delivery.id
    assert uow.pending_events[1].id == second_delivery.id


def test_handle_uses_none_admin_unit_id_when_event_has_no_attribute(monkeypatch):
    handler = (
        app_installation_webhook_event_handler.AppInstallationWebhookEventHandler()
    )

    class DummyEvent:
        def __init__(self):
            self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    dummy_event = DummyEvent()
    uow = _FakeUow(installations=[])
    info = _fake_webhook_info("dummy.event")

    monkeypatch.setitem(
        app_installation_webhook_event_handler._EVENT_WEBHOOK_EVENT_TYPE,
        DummyEvent,
        "dummy.event",
    )
    monkeypatch.setattr(
        app_installation_webhook_event_handler,
        "get_app_installation_webhook_info_by_event_type",
        Mock(return_value=info),
    )

    handler.handle(dummy_event, uow)

    uow.organizations.get_app_installations_with_webhook.assert_called_once_with(
        None,
        info.permissions,
        info.event_type,
    )
