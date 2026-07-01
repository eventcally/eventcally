"""Unit tests for AppWebhookEventHandler."""

from unittest.mock import MagicMock, patch

from project.application.event_handlers.app_webhook_event_handler import (
    AppWebhookEventHandler,
)
from project.domain import events
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types.changed_value import ChangedValue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_webhook(enabled=True):
    if enabled:
        return WebhookValueObject(
            url="https://example.com/hook",
            event_types=["app_installation.permissions_updated"],
        )
    return WebhookValueObject(url="", disabled=True)


def _make_app_with_webhook(uow, webhook=None, app_id=None):
    app = AppAggregate.create(
        actor=Actor(),
        admin_unit_id=1,
        name="App",
        app_permissions=["events:read"],
    )
    uow.apps.add(app)
    if app_id is not None:
        app.id = app_id
    app.webhook = webhook
    return app


def _make_event(event_type_key="app.installed", app_id=1):
    pass


def _make_permissions_updated_event(app_id=1):
    return events.AppInstallationPermissionsUpdated(
        actor=Actor(),
        id=1,
        admin_unit_id=2,
        app_id=app_id,
        permissions=ChangedValue(old=set(), new={"events:read"}),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAppWebhookEventHandler:
    def _handler(self):
        return AppWebhookEventHandler(mapper_context=MagicMock())

    def test_app_not_found_returns_early(self, uow):
        ev = _make_permissions_updated_event(app_id=9999)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 0

    def test_app_has_no_webhook_returns_early(self, uow):
        app = _make_app_with_webhook(uow, webhook=None)
        ev = _make_permissions_updated_event(app_id=app.id)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 0

    def test_webhook_disabled_for_event_type_returns_early(self, uow):
        webhook = _make_webhook(enabled=False)
        app = _make_app_with_webhook(uow, webhook=webhook)
        ev = _make_permissions_updated_event(app_id=app.id)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 0

    def test_happy_path_creates_webhook_event_and_delivery(self, uow):
        webhook = _make_webhook(enabled=True)
        app = _make_app_with_webhook(uow, webhook=webhook)
        ev = _make_permissions_updated_event(app_id=app.id)

        mock_payload = MagicMock()
        mock_payload.model_dump.return_value = {}
        with patch("project.application.webhooks.app_webhooks.app_webhook_infos"):
            fake_info = MagicMock()
            fake_info.event_type = "app_installation.permissions_updated"
            fake_info.payload_cls = MagicMock(return_value=mock_payload)
            fake_info.payload_cls.from_event.return_value = mock_payload

            with patch(
                "project.application.event_handlers.app_webhook_event_handler.get_app_webhook_info_by_event_type",
                return_value=fake_info,
            ):
                self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1
        assert len(uow.webhook_deliveries._store) == 1

    def test_app_installation_deleted_event_type(self, uow):
        webhook = _make_webhook(enabled=False)
        app = AppAggregate.create(
            actor=Actor(), admin_unit_id=1, name="App", app_permissions=["x"]
        )
        uow.apps.add(app)
        app.webhook = webhook

        ev = events.AppInstallationDeleted(
            actor=Actor(),
            id=1,
            admin_unit_id=2,
            app_id=app.id,
        )
        self._handler().handle(ev, uow)

        # webhook is not enabled for this event type → early return
        assert len(uow.webhook_events._store) == 0

    def test_app_installation_permissions_updated_event_type(self, uow):
        webhook = _make_webhook(enabled=True)
        app = AppAggregate.create(
            actor=Actor(), admin_unit_id=1, name="App", app_permissions=["x"]
        )
        uow.apps.add(app)
        app.webhook = webhook

        ev = events.AppInstallationPermissionsUpdated(
            actor=Actor(),
            id=1,
            admin_unit_id=2,
            app_id=app.id,
            permissions=ChangedValue(old=set(), new={"events:read"}),
        )
        mock_payload = MagicMock()
        mock_payload.model_dump.return_value = {}
        fake_info = MagicMock()
        fake_info.event_type = "app_installation.permissions_updated"
        fake_info.payload_cls.from_event.return_value = mock_payload

        with patch(
            "project.application.event_handlers.app_webhook_event_handler.get_app_webhook_info_by_event_type",
            return_value=fake_info,
        ):
            self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1
