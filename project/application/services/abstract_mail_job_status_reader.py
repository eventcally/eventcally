import abc
from typing import Optional

from project.application.read_models.mail_job_read_models import MailJobStatusReadModel


class AbstractMailJobStatusReader(abc.ABC):
    @abc.abstractmethod
    def get(self, job_id: str) -> Optional[MailJobStatusReadModel]:  # pragma: no cover
        """None for unknown or expired jobs."""
        raise NotImplementedError
