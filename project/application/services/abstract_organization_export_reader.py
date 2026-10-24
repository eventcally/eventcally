import abc
from typing import Optional

from project.application.read_models.organization_export_read_models import (
    OrganizationExportFile,
    OrganizationExportJobStatusReadModel,
)
from project.domain.types import ObjectId


class AbstractOrganizationExportReader(abc.ABC):
    @abc.abstractmethod
    def get_file(
        self, admin_unit_id: ObjectId
    ) -> Optional[OrganizationExportFile]:  # pragma: no cover
        """None if no export has been created."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_job_status(
        self, job_id: str
    ) -> OrganizationExportJobStatusReadModel:  # pragma: no cover
        raise NotImplementedError
