"""Unit tests for AppInstallationWebhookEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.app_installation_webhook_event_handler import (
    AppInstallationWebhookEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# Helpers — fake installation with oauth2_client attributes
# ---------------------------------------------------------------------------


class _FakeWebhook:
    id = 99


class _FakeOAuth2Client:
    webhook_id = 99


class _FakeInstallation:
    """Mimics AppInstallation SQLAlchemy model attributes accessed by the handler."""

    def __init__(self, installation_id=1, app_id=10):
        self.id = installation_id
        self.oauth2_client_id = app_id
        self.oauth2_client = _FakeOAuth2Client()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAppInstallationWebhookEventHandler:
    def _handler(self):
        return AppInstallationWebhookEventHandler(mapper_context=MagicMock())

    def _make_event(self, event_cls):
        actor = Actor()
        return event_cls(actor=actor, id=1, admin_unit_id=2, name="Org")

    def test_no_installations_returns_early_no_webhook_event_created(self, uow):
        """When get_all_with_webhook returns [], no webhook event is persisted."""
        uow.organization_app_installations._webhook_installations = []

        ev = events.EventOrganizerCreated(
            actor=Actor(), id=1, admin_unit_id=2, name="Org"
        )
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 0

    def test_with_installation_creates_webhook_event_and_delivery(self, uow):
        """When there is a matching installation, creates WebhookEvent + Delivery."""
        installation = _FakeInstallation(installation_id=5, app_id=10)
        uow.organization_app_installations._webhook_installations = [installation]

        ev = events.EventOrganizerCreated(
            actor=Actor(), id=1, admin_unit_id=2, name="Org"
        )
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1
        assert len(uow.webhook_deliveries._store) == 1
        assert uow.committed

    def test_multiple_installations_create_multiple_deliveries(self, uow):
        inst1 = _FakeInstallation(installation_id=1, app_id=10)
        inst2 = _FakeInstallation(installation_id=2, app_id=11)
        uow.organization_app_installations._webhook_installations = [inst1, inst2]

        ev = events.EventOrganizerCreated(
            actor=Actor(), id=1, admin_unit_id=2, name="Org"
        )
        self._handler().handle(ev, uow)

        assert len(uow.webhook_deliveries._store) == 2

    def test_event_place_created_event_type(self, uow):
        """Ensure EventPlaceCreated is also handled (different event type key)."""
        installation = _FakeInstallation()
        uow.organization_app_installations._webhook_installations = [installation]

        ev = events.EventPlaceCreated(
            actor=Actor(), id=1, admin_unit_id=2, name="Place"
        )
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1

    def test_event_organizer_updated_event_type(self, uow):
        installation = _FakeInstallation()
        uow.organization_app_installations._webhook_installations = [installation]

        ev = events.EventOrganizerUpdated(actor=Actor(), id=1, admin_unit_id=2)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1

    def test_event_organizer_deleted_event_type(self, uow):
        installation = _FakeInstallation()
        uow.organization_app_installations._webhook_installations = [installation]

        ev = events.EventOrganizerDeleted(actor=Actor(), id=1, admin_unit_id=2)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1

    def test_event_place_updated_event_type(self, uow):
        installation = _FakeInstallation()
        uow.organization_app_installations._webhook_installations = [installation]

        ev = events.EventPlaceUpdated(actor=Actor(), id=1, admin_unit_id=2)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1

    def test_event_place_deleted_event_type(self, uow):
        installation = _FakeInstallation()
        uow.organization_app_installations._webhook_installations = [installation]

        ev = events.EventPlaceDeleted(actor=Actor(), id=1, admin_unit_id=2)
        self._handler().handle(ev, uow)

        assert len(uow.webhook_events._store) == 1
