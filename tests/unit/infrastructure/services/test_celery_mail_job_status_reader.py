from unittest.mock import MagicMock

from project.infrastructure.services.celery_mail_job_status_reader import (
    CeleryMailJobStatusReader,
)

RESTORE = (
    "project.infrastructure.services.celery_mail_job_status_reader.GroupResult.restore"
)


def _group(ready, successful, completed, count=3):
    result = MagicMock()
    result.children = [object()] * count
    result.ready.return_value = ready
    result.successful.return_value = successful
    result.completed_count.return_value = completed
    return result


def test_unknown_job_is_none(mocker):
    mocker.patch(RESTORE, return_value=None)

    assert CeleryMailJobStatusReader().get("abc") is None


def test_running_job(mocker):
    mocker.patch(RESTORE, return_value=_group(False, False, 1))

    status = CeleryMailJobStatusReader().get("abc")

    assert status.job_id == "abc"
    assert (status.count, status.completed, status.ready) == (3, 1, False)
    assert status.successful is None


def test_done_job(mocker):
    mocker.patch(RESTORE, return_value=_group(True, True, 3))

    status = CeleryMailJobStatusReader().get("abc")

    assert status.ready is True
    assert status.successful is True


def test_done_job_with_failure(mocker):
    mocker.patch(RESTORE, return_value=_group(True, False, 3))

    status = CeleryMailJobStatusReader().get("abc")

    assert status.ready is True
    assert status.successful is False
