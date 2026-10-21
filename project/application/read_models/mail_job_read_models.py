"""Read models of tracked mail sends."""

from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class MailJob(BaseReadModel):
    """A queued batch of mails. `job_id` is None when there is nothing to track
    (no recipients, or the mails were already sent eagerly)."""

    model_config = ConfigDict(frozen=True)

    job_id: Optional[str] = None
    count: int = 0


class MailJobStatusReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    count: int
    completed: int
    ready: bool
    successful: Optional[bool] = None
