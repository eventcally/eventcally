"""Export job ids carry the organization id, so a status poll only answers for the
jobs of that organization."""

import uuid

from project.domain.types import ObjectId

PREFIX = "org-export-"


def new_organization_export_job_id(admin_unit_id: ObjectId) -> str:
    return f"{PREFIX}{admin_unit_id}-{uuid.uuid4()}"


def is_organization_export_job_id(admin_unit_id: ObjectId, job_id: str) -> bool:
    prefix = f"{PREFIX}{admin_unit_id}-"
    if not job_id.startswith(prefix):
        return False

    try:
        uuid.UUID(job_id[len(prefix) :])
    except ValueError:
        return False

    return True
