from datetime import timezone

import pytest

from project.infrastructure.services import file_system_organization_export_reader
from project.infrastructure.services.file_system_organization_export_reader import (
    FileSystemOrganizationExportReader,
)


@pytest.fixture
def dump_dir(tmp_path, mocker):
    mocker.patch.object(
        file_system_organization_export_reader, "dump_org_path", str(tmp_path)
    )
    return tmp_path


def test_get_file_without_export_is_none(dump_dir):
    assert FileSystemOrganizationExportReader().get_file(5) is None


def test_get_file_reads_size_and_creation_time(dump_dir):
    (dump_dir / "org-5.zip").write_bytes(b"x" * 42)

    export_file = FileSystemOrganizationExportReader().get_file(5)

    assert export_file.size == 42
    assert export_file.created_at.tzinfo == timezone.utc
    assert FileSystemOrganizationExportReader().get_file(6) is None


class _Result:
    def __init__(self, ready, successful=None):
        self._ready = ready
        self._successful = successful

    def ready(self):
        return self._ready

    def successful(self):
        return self._successful


@pytest.mark.parametrize(
    "result,ready,successful",
    [
        (_Result(False), False, None),
        (_Result(True, True), True, True),
        (_Result(True, False), True, False),
    ],
)
def test_get_job_status(app, mocker, result, ready, successful):
    from project.infrastructure.celery_app import celery

    mocker.patch.object(celery, "AsyncResult", return_value=result)

    status = FileSystemOrganizationExportReader().get_job_status("job")

    assert (status.job_id, status.ready, status.successful) == (
        "job",
        ready,
        successful,
    )


def test_get_job_status_backend_error_is_failed(app, mocker):
    from project.infrastructure.celery_app import celery

    mocker.patch.object(celery, "AsyncResult", side_effect=Exception("down"))

    status = FileSystemOrganizationExportReader().get_job_status("job")

    assert status.ready is True
    assert status.successful is False
