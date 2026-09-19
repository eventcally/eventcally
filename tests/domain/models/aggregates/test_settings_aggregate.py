import pytest

from project.domain.models.aggregates.settings_aggregate import SettingsAggregate
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestSettingsAggregateCreate:
    def test_creates_instance(self, actor):
        settings = SettingsAggregate.create(actor=actor)
        assert settings.id == -1
        assert settings.tos is None
        assert settings.legal_notice is None
        assert settings.contact is None
        assert settings.privacy is None
        assert settings.start_page is None
        assert settings.announcement is None
        assert settings.planning_external_calendars is None


class TestSettingsAggregateUpdate:
    def test_updates_site_settings_fields(self, actor):
        settings = SettingsAggregate(id=1)
        settings.update(
            actor=actor,
            tos="Terms",
            legal_notice="Legal notice",
            contact="Contact",
            privacy="Privacy",
            start_page="Start page",
            announcement="Announcement",
        )
        assert settings.tos == "Terms"
        assert settings.legal_notice == "Legal notice"
        assert settings.contact == "Contact"
        assert settings.privacy == "Privacy"
        assert settings.start_page == "Start page"
        assert settings.announcement == "Announcement"

    def test_updates_planning_external_calendars(self, actor):
        settings = SettingsAggregate(id=1)
        settings.update(actor=actor, planning_external_calendars="[]")
        assert settings.planning_external_calendars == "[]"

    def test_leaves_omitted_fields_untouched(self, actor):
        settings = SettingsAggregate(id=1)
        settings.update(actor=actor, tos="Terms")
        settings.update(actor=actor, contact="Contact")

        assert settings.tos == "Terms"
        assert settings.contact == "Contact"

    def test_can_clear_field_to_none(self, actor):
        settings = SettingsAggregate(id=1)
        settings.update(actor=actor, tos="Terms")
        settings.update(actor=actor, tos=None)
        assert settings.tos is None
