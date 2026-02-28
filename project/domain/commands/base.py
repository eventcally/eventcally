from typing import Generic, TypeVar

from pydantic import BaseModel

from project.domain.types import Actor


class Command(BaseModel):
    actor: Actor


class CommandResult(BaseModel):
    pass


CommandResultType = TypeVar("CommandResult")


class CommandWithResult(Command, Generic[CommandResultType]):
    pass
