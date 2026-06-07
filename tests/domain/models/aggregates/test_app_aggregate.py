import pytest

from project.domain.events.app_created import AppCreated
from project.domain.events.app_deleted import AppDeleted
from project.domain.events.app_updated import AppUpdated
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types.changed_value import ChangedValue


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def app(actor):
    return AppAggregate.create(
        actor=actor,
        admin_unit_id=2,
        name="My App",
        app_permissions=["read"],
    )


class TestAppAggregateCreate:
    def test_creates_instance(self, actor):
        app = AppAggregate.create(
            actor=actor, admin_unit_id=2, name="App", app_permissions=["write"]
        )
        assert app.name == "App"
        assert app.admin_unit_id == 2
        assert app.app_permissions == ["write"]

    def test_appends_created_event(self, actor):
        app = AppAggregate.create(
            actor=actor, admin_unit_id=2, name="App", app_permissions=[]
        )
        assert len(app.domain_events) == 1
        assert isinstance(app.domain_events[0], AppCreated)

    def test_created_event_has_correct_name(self, actor):
        app = AppAggregate.create(
            actor=actor, admin_unit_id=2, name="App", app_permissions=[]
        )
        assert app.domain_events[0].name == "App"

    def test_optional_fields_default_none(self, actor):
        app = AppAggregate.create(
            actor=actor, admin_unit_id=2, name="App", app_permissions=[]
        )
        assert app.redirect_uris is None
        assert app.scope is None
        assert app.description is None
        assert app.homepage_url is None
        assert app.setup_url is None
        assert app.webhook is None

    def test_create_with_webhook(self, actor):
        webhook = WebhookValueObject(url="https://example.com/hook")
        app = AppAggregate.create(
            actor=actor,
            admin_unit_id=2,
            name="App",
            app_permissions=[],
            webhook=webhook,
        )
        assert app.webhook is webhook


class TestAppAggregateUpdate:
    def test_update_with_no_changes_appends_no_event(self, app, actor):
        initial_count = len(app.domain_events)
        app.update(actor=actor)
        assert len(app.domain_events) == initial_count

    def test_update_name_appends_updated_event(self, app, actor):
        initial_count = len(app.domain_events)
        app.update(actor=actor, name="New Name")
        assert len(app.domain_events) == initial_count + 1
        assert isinstance(app.domain_events[-1], AppUpdated)

    def test_update_name_sets_changed_value(self, app, actor):
        app.update(actor=actor, name="Updated App")
        event = app.domain_events[-1]
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "My App"
        assert event.name.new == "Updated App"

    def test_update_app_permissions_sets_changed_value(self, app, actor):
        app.update(actor=actor, app_permissions=["read", "write"])
        event = app.domain_events[-1]
        assert isinstance(event.app_permissions, ChangedValue)
        assert event.app_permissions.new == ["read", "write"]

    def test_update_webhook_sets_changed_value(self, app, actor):
        webhook = WebhookValueObject(url="https://example.com")
        app.update(actor=actor, webhook=webhook)
        event = app.domain_events[-1]
        assert isinstance(event.webhook, ChangedValue)
        assert event.webhook.new.url == "https://example.com"

    def test_update_same_name_appends_no_event(self, app, actor):
        initial_count = len(app.domain_events)
        app.update(actor=actor, name="My App")
        assert len(app.domain_events) == initial_count


class TestAppAggregateDeleteApp:
    def test_delete_app_appends_deleted_event(self, app, actor):
        initial_count = len(app.domain_events)
        app.delete_app(actor=actor)
        assert len(app.domain_events) == initial_count + 1
        assert isinstance(app.domain_events[-1], AppDeleted)

    def test_deleted_event_ids(self, app, actor):
        app.delete_app(actor=actor)
        event = app.domain_events[-1]
        assert event.id == app.id
        assert event.admin_unit_id == app.admin_unit_id
