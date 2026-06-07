import pytest
from pydantic import ValidationError

from project.application.commands.update_app_command import UpdateAppCommand
from project.application.commands.update_event_command import UpdateEventCommand
from project.domain.models.entities.actor import Actor
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class AliasModel(CustomBaseModel):
    required_value: Unsetable[str] = UnsetField()
    nullable_value: NullableUnsetable[str] = UnsetField()


def test_unsetable_rejects_none():
    with pytest.raises(ValidationError):
        AliasModel(required_value=None)


def test_nullable_unsetable_accepts_none():
    model = AliasModel(nullable_value=None)

    assert model.nullable_value is None


def test_update_event_command_accepts_none_for_nullable_fields():
    command = UpdateEventCommand(
        id=1,
        actor=Actor(user_id=1),
        description=None,
        previous_start_date=None,
    )

    assert command.id == 1
    assert command.description is None
    assert command.previous_start_date is None


def test_update_event_command_rejects_none_for_non_nullable_fields():
    with pytest.raises(ValidationError):
        UpdateEventCommand(id=1, actor=Actor(user_id=1), name=None)


def test_update_app_command_accepts_none_for_nullable_fields():
    command = UpdateAppCommand(
        id=1,
        actor=Actor(user_id=1),
        app_permissions=["read", "write"],
        description=None,
        webhook=None,
    )

    assert command.id == 1
    assert command.app_permissions == ["read", "write"]
    assert command.description is None
    assert command.webhook is None
