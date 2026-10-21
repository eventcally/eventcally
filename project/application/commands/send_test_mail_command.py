from typing import Optional

from .base import CommandResult, CommandWithResult


class SendTestMailCommandResult(CommandResult):
    job_id: Optional[str] = None
    count: int


class SendTestMailCommand(CommandWithResult[SendTestMailCommandResult]):
    recipient: str
    asynchronous: bool = False
