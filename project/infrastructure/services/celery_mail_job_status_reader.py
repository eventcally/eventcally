from typing import Optional

from celery.result import GroupResult

from project.application.read_models.mail_job_read_models import MailJobStatusReadModel
from project.application.services.abstract_mail_job_status_reader import (
    AbstractMailJobStatusReader,
)


class CeleryMailJobStatusReader(AbstractMailJobStatusReader):
    def get(self, job_id: str) -> Optional[MailJobStatusReadModel]:
        from project.infrastructure.celery_app import celery

        result = GroupResult.restore(job_id, app=celery)
        if result is None:
            return None

        ready = result.ready()
        return MailJobStatusReadModel(
            job_id=job_id,
            count=len(result.children),
            completed=result.completed_count(),
            ready=ready,
            successful=result.successful() if ready else None,
        )
