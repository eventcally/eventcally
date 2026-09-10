import pytest

from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def widget(actor):
    return CustomWidgetAggregate.create(
        actor=actor,
        admin_unit_id=2,
        widget_type="search",
        name="Test Widget",
        settings={"color": "black"},
    )


class TestCustomWidgetAggregateCreate:
    def test_creates_instance(self, actor):
        widget = CustomWidgetAggregate.create(
            actor=actor, admin_unit_id=2, widget_type="search", name="Widget"
        )
        assert widget.id == -1
        assert widget.admin_unit_id == 2
        assert widget.widget_type == "search"
        assert widget.name == "Widget"

    def test_settings_default_none(self, actor):
        widget = CustomWidgetAggregate.create(
            actor=actor, admin_unit_id=2, widget_type="search", name="Widget"
        )
        assert widget.settings is None

    def test_create_with_settings(self, actor):
        widget = CustomWidgetAggregate.create(
            actor=actor,
            admin_unit_id=2,
            widget_type="search",
            name="Widget",
            settings={"color": "red"},
        )
        assert widget.settings == {"color": "red"}


class TestCustomWidgetAggregateUpdate:
    def test_update_with_no_changes_leaves_fields_untouched(self, widget, actor):
        widget.update(actor=actor)
        assert widget.widget_type == "search"
        assert widget.name == "Test Widget"
        assert widget.settings == {"color": "black"}

    def test_update_widget_type(self, widget, actor):
        widget.update(actor=actor, widget_type="list")
        assert widget.widget_type == "list"

    def test_update_name(self, widget, actor):
        widget.update(actor=actor, name="New Name")
        assert widget.name == "New Name"

    def test_update_settings(self, widget, actor):
        widget.update(actor=actor, settings={"color": "blue"})
        assert widget.settings == {"color": "blue"}

    def test_update_settings_to_none_clears_field(self, widget, actor):
        widget.update(actor=actor, settings=None)
        assert widget.settings is None


class TestCustomWidgetAggregateDelete:
    def test_delete_does_not_raise(self, widget, actor):
        widget.delete(actor=actor)
