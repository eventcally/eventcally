from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.mail_job_read_models import MailJobStatusReadModel


class GetMailJobStatusQuery(Query[Optional[MailJobStatusReadModel]]):
    """Platform admins only. `None` for unknown or expired jobs."""

    job_id: str
