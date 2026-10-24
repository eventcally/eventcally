import uuid

import pytest

from project.application.services.organization_export_jobs import (
    is_organization_export_job_id,
    new_organization_export_job_id,
)


def test_new_job_id_carries_the_organization():
    job_id = new_organization_export_job_id(12)

    assert job_id.startswith("org-export-12-")
    uuid.UUID(job_id[len("org-export-12-") :])


def test_new_job_ids_are_unique():
    assert new_organization_export_job_id(1) != new_organization_export_job_id(1)


def test_own_job_id_matches():
    assert is_organization_export_job_id(12, new_organization_export_job_id(12))


@pytest.mark.parametrize(
    "job_id",
    [
        "org-export-1-6c1f3d4e-7a3b-4a57-9f55-2a8f0f0c9a11",
        "org-export-12-",
        "org-export-12-not-a-uuid",
        "org-export-12",
        "6c1f3d4e-7a3b-4a57-9f55-2a8f0f0c9a11",
        "",
    ],
)
def test_other_job_ids_do_not_match(job_id):
    assert not is_organization_export_job_id(12, job_id)
