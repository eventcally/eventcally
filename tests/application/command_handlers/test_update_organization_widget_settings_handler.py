"""Unit tests for UpdateOrganizationWidgetSettingsHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.update_organization_widget_settings_handler import (
    UpdateOrganizationWidgetSettingsHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, grant_permission


def _make_organization(uow):
    org = OrganizationAggregate.create(
        actor=Actor(), name="My Crew", short_name="my_crew"
    )
    uow.organizations.add(org)
    return org


class TestUpdateOrganizationWidgetSettingsHandler:
    def test_updates_widget_fields(self, uow):
        org = _make_organization(uow)
        grant_permission(uow, org.id, "widgets:write")
        cmd = commands.UpdateOrganizationWidgetSettingsCommand.model_construct(
            actor=ACTOR,
            id=org.id,
            widget_font="Arial",
            widget_background_color="#000000",
            widget_primary_color="#111111",
            widget_link_color="#222222",
        )

        UpdateOrganizationWidgetSettingsHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.widget_font == "Arial"
        assert updated.widget_background_color == "#000000"
        assert updated.widget_primary_color == "#111111"
        assert updated.widget_link_color == "#222222"

    def test_field_can_be_cleared(self, uow):
        org = _make_organization(uow)
        grant_permission(uow, org.id, "widgets:write")
        set_cmd = commands.UpdateOrganizationWidgetSettingsCommand.model_construct(
            actor=ACTOR, id=org.id, widget_background_color="#000000"
        )
        UpdateOrganizationWidgetSettingsHandler().handle(set_cmd, uow)

        clear_cmd = commands.UpdateOrganizationWidgetSettingsCommand.model_construct(
            actor=ACTOR, id=org.id, widget_background_color=None
        )
        UpdateOrganizationWidgetSettingsHandler().handle(clear_cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.widget_background_color is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateOrganizationWidgetSettingsCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            UpdateOrganizationWidgetSettingsHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        org = _make_organization(uow)
        cmd = commands.UpdateOrganizationWidgetSettingsCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        with pytest.raises(UnauthorizedError):
            UpdateOrganizationWidgetSettingsHandler().handle(cmd, uow)
