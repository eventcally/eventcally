import os
from datetime import datetime, timezone
from typing import Optional

from project.application.read_models.organization_export_read_models import (
    OrganizationExportFile,
    OrganizationExportJobStatusReadModel,
)
from project.application.services.abstract_organization_export_reader import (
    AbstractOrganizationExportReader,
)
from project.domain.types import ObjectId
from project.shared.paths import dump_org_path


class FileSystemOrganizationExportReader(AbstractOrganizationExportReader):
    def get_file(self, admin_unit_id: ObjectId) -> Optional[OrganizationExportFile]:
        file_path = os.path.join(dump_org_path, f"org-{admin_unit_id}.zip")

        if not os.path.exists(file_path):
            return None

        return OrganizationExportFile(
            size=os.path.getsize(file_path),
            created_at=datetime.fromtimestamp(
                os.path.getctime(file_path), tz=timezone.utc
            ),
        )

    def get_job_status(self, job_id: str) -> OrganizationExportJobStatusReadModel:
        from project.infrastructure.celery_app import celery

        try:
            result = celery.AsyncResult(job_id)
            ready = result.ready()
            successful = result.successful() if ready else None
        except Exception:
            # An unreachable backend or an unreadable result ends the poll as failed.
            return OrganizationExportJobStatusReadModel(
                job_id=job_id, ready=True, successful=False
            )

        return OrganizationExportJobStatusReadModel(
            job_id=job_id, ready=ready, successful=successful
        )
