from typing import Generic, TypeVar

from project.domain.types import Actor
from project.domain.types.custom_base_model import CustomBaseModel


class Command(CustomBaseModel):
    actor: Actor


class CommandResult(CustomBaseModel):
    pass


CommandResultType = TypeVar("CommandResult")


class CommandWithResult(Command, Generic[CommandResultType]):
    pass
