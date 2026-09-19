"""Unit tests for custom widget command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_custom_widget_handler import (
    CreateCustomWidgetHandler,
)
from project.application.command_handlers.delete_custom_widget_handler import (
    DeleteCustomWidgetHandler,
)
from project.application.command_handlers.update_custom_widget_handler import (
    UpdateCustomWidgetHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, grant_permission

# ---------------------------------------------------------------------------
# CreateCustomWidgetHandler
# ---------------------------------------------------------------------------


class TestCreateCustomWidgetHandler:
    def test_creates_widget_and_returns_result(self, uow):
        grant_permission(uow, 1, "custom_widgets:write")
        cmd = commands.CreateCustomWidgetCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=1,
            widget_type="search",
            name="Test Widget",
            settings={"color": "black"},
        )

        result = CreateCustomWidgetHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.custom_widgets.get(result.id)
        assert created is not None
        assert created.name == "Test Widget"
        assert created.widget_type == "search"
        assert created.settings == {"color": "black"}

    def test_settings_round_trips_through_strict_validation(self, uow):
        grant_permission(uow, 1, "custom_widgets:write")
        cmd = commands.CreateCustomWidgetCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=1,
            widget_type="search",
            name="Test Widget",
            settings={"color": "black"},
        )
        cmd.model_validate(cmd.model_dump(round_trip=True), strict=True)

        result = CreateCustomWidgetHandler().handle(cmd, uow)

        assert result.id > 0

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.CreateCustomWidgetCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=1,
            widget_type="search",
            name="Test Widget",
            settings=None,
        )

        with pytest.raises(UnauthorizedError):
            CreateCustomWidgetHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateCustomWidgetHandler
# ---------------------------------------------------------------------------


class TestUpdateCustomWidgetHandler:
    def _seed(self, uow):
        widget = CustomWidgetAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            widget_type="search",
            name="Old Name",
        )
        uow.custom_widgets.add(widget)
        return widget

    def test_updates_widget(self, uow):
        widget = self._seed(uow)
        grant_permission(uow, 1, "custom_widgets:write")
        cmd = commands.UpdateCustomWidgetCommand.model_construct(
            actor=ACTOR, id=widget.id, name="New Name"
        )

        UpdateCustomWidgetHandler().handle(cmd, uow)

        updated = uow.custom_widgets.get(widget.id)
        assert updated.name == "New Name"

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateCustomWidgetCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            UpdateCustomWidgetHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        widget = self._seed(uow)
        cmd = commands.UpdateCustomWidgetCommand.model_construct(
            actor=ACTOR, id=widget.id, name="New Name"
        )

        with pytest.raises(UnauthorizedError):
            UpdateCustomWidgetHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteCustomWidgetHandler
# ---------------------------------------------------------------------------


class TestDeleteCustomWidgetHandler:
    def _seed(self, uow):
        widget = CustomWidgetAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            widget_type="search",
            name="To Delete",
        )
        uow.custom_widgets.add(widget)
        return widget

    def test_removes_widget(self, uow):
        widget = self._seed(uow)
        widget_id = widget.id
        grant_permission(uow, 1, "custom_widgets:write")

        cmd = commands.DeleteCustomWidgetCommand.model_construct(
            actor=ACTOR, id=widget_id
        )
        DeleteCustomWidgetHandler().handle(cmd, uow)

        assert uow.custom_widgets.get(widget_id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteCustomWidgetCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            DeleteCustomWidgetHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        widget = self._seed(uow)
        cmd = commands.DeleteCustomWidgetCommand.model_construct(
            actor=ACTOR, id=widget.id
        )

        with pytest.raises(UnauthorizedError):
            DeleteCustomWidgetHandler().handle(cmd, uow)
