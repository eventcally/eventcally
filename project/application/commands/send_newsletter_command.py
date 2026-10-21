from typing import Literal, Optional

from pydantic import Field, model_validator

from .base import CommandResult, CommandWithResult


class SendNewsletterCommandResult(CommandResult):
    job_id: Optional[str] = None
    count: int


class SendNewsletterCommand(CommandWithResult[SendNewsletterCommandResult]):
    """`audience` is explicit: a missing recipient must never mean "everyone"."""

    audience: Literal["test", "all"]
    test_recipient: Optional[str] = None
    message: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_test_recipient(self):
        if self.audience == "test" and not self.test_recipient:
            raise ValueError("test_recipient is required for the test audience")
        if self.audience == "all" and self.test_recipient is not None:
            raise ValueError("test_recipient must not be set for the all audience")
        return self
