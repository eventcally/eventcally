"""Unit tests for application command classes."""

import pytest

from project.application import commands
from project.domain.models.entities.actor import Actor


class TestCommandBase:
    def test_command_has_actor_field(self):
        cmd = commands.CreateEventOrganizerCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="Test",
            url=None,
            email=None,
            phone=None,
            fax=None,
            location=None,
            logo=None,
        )
        assert hasattr(cmd, "actor")

    def test_command_with_result_is_generic(self):
        # CreateEventCommand is CommandWithResult[CreateEventCommandResult]
        from project.application.commands.base import CommandWithResult
        from project.application.commands.create_event_command import CreateEventCommand

        assert issubclass(CreateEventCommand, CommandWithResult)


class TestCreateEventCommandResult:
    def test_id_field(self):
        from project.application.commands.create_event_command import (
            CreateEventCommandResult,
        )

        result = CreateEventCommandResult(id=42)
        assert result.id == 42


class TestCreateEventOrganizerCommandResult:
    def test_id_field(self):
        from project.application.commands.create_event_organizer_command import (
            CreateEventOrganizerCommandResult,
        )

        result = CreateEventOrganizerCommandResult(id=7)
        assert result.id == 7


class TestCreateEventPlaceCommandResult:
    def test_id_field(self):
        from project.application.commands.create_event_place_command import (
            CreateEventPlaceCommandResult,
        )

        result = CreateEventPlaceCommandResult(id=3)
        assert result.id == 3


class TestCreateAppCommandResult:
    def test_id_field(self):
        from project.application.commands.create_app_command import (
            CreateAppCommandResult,
        )

        result = CreateAppCommandResult(id=99)
        assert result.id == 99


class TestInstallAppCommandResult:
    def test_id_field(self):
        from project.application.commands.install_app_command import (
            InstallAppCommandResult,
        )

        result = InstallAppCommandResult(id=55)
        assert result.id == 55


class TestUpdateAppCommand:
    def test_empty_app_permissions_raises(self):
        from project.application.commands.update_app_command import UpdateAppCommand

        with pytest.raises(ValueError, match="app_permissions must contain"):
            UpdateAppCommand(
                actor=Actor(),
                id=1,
                app_permissions=[],
            )

    def test_non_empty_app_permissions_is_valid(self):
        from project.application.commands.update_app_command import UpdateAppCommand

        cmd = UpdateAppCommand(
            actor=Actor(),
            id=1,
            app_permissions=["events:read"],
        )
        assert cmd.app_permissions == ["events:read"]
