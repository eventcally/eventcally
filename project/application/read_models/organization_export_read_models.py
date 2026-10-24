"""Read models of the organization data export."""

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class OrganizationExportFile(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    size: int
    created_at: datetime


class OrganizationExportReadModel(BaseReadModel):
    """`file` is None while no export has been created."""

    model_config = ConfigDict(frozen=True)

    file: Optional[OrganizationExportFile] = None


class OrganizationExportJobStatusReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    ready: bool
    successful: Optional[bool] = None
