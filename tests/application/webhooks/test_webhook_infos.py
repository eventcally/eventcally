"""Unit tests for webhook info functions."""

from project.application.webhooks.app_installation_webhooks import (
    app_installation_webhook_infos,
    get_app_installation_webhook_info_by_event_type,
)
from project.application.webhooks.app_webhooks import (
    app_webhook_infos,
    get_app_webhook_info_by_event_type,
)


class TestAppInstallationWebhookInfos:
    def test_get_by_event_type_event_organizer_created(self):
        info = get_app_installation_webhook_info_by_event_type(
            "event_organizer.created"
        )
        assert info is not None
        assert info.event_type == "event_organizer.created"
        assert "event_organizers:read" in info.permissions

    def test_get_by_event_type_event_organizer_updated(self):
        info = get_app_installation_webhook_info_by_event_type(
            "event_organizer.updated"
        )
        assert info is not None

    def test_get_by_event_type_event_organizer_deleted(self):
        info = get_app_installation_webhook_info_by_event_type(
            "event_organizer.deleted"
        )
        assert info is not None

    def test_get_by_event_type_event_place_created(self):
        info = get_app_installation_webhook_info_by_event_type("event_place.created")
        assert info is not None
        assert "event_places:read" in info.permissions

    def test_get_by_event_type_event_place_updated(self):
        info = get_app_installation_webhook_info_by_event_type("event_place.updated")
        assert info is not None

    def test_get_by_event_type_event_place_deleted(self):
        info = get_app_installation_webhook_info_by_event_type("event_place.deleted")
        assert info is not None

    def test_get_by_event_type_nonexistent_returns_none(self):
        result = get_app_installation_webhook_info_by_event_type("nonexistent.type")
        assert result is None

    def test_all_infos_have_payload_cls(self):
        for info in app_installation_webhook_infos:
            assert info.payload_cls is not None


class TestAppWebhookInfos:
    def test_get_by_event_type_app_installed(self):
        info = get_app_webhook_info_by_event_type("app.installed")
        assert info is not None
        assert info.event_type == "app.installed"

    def test_get_by_event_type_app_uninstalled(self):
        info = get_app_webhook_info_by_event_type("app.uninstalled")
        assert info is not None

    def test_get_by_event_type_app_installation_permissions_updated(self):
        info = get_app_webhook_info_by_event_type(
            "app_installation.permissions_updated"
        )
        assert info is not None

    def test_get_by_event_type_nonexistent_returns_none(self):
        result = get_app_webhook_info_by_event_type("nonexistent")
        assert result is None

    def test_all_infos_have_payload_cls(self):
        for info in app_webhook_infos:
            assert info.payload_cls is not None
