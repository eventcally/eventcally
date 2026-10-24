import pytest

from project.infrastructure.celery_app import celery
from project.infrastructure.services.celery_organization_export_dispatcher import (
    DUMP_TASK_NAME,
    CeleryOrganizationExportDispatcher,
)


@pytest.mark.parametrize("eager", [True, False])
def test_start_applies_the_dump_task_under_the_job_id(app, mocker, eager):
    apply_async = mocker.patch.object(celery.tasks[DUMP_TASK_NAME], "apply_async")
    original = celery.conf.task_always_eager
    celery.conf.task_always_eager = eager

    try:
        tracked = CeleryOrganizationExportDispatcher().start(5, "org-export-5-abc")
    finally:
        celery.conf.task_always_eager = original

    apply_async.assert_called_once_with(args=[5], task_id="org-export-5-abc")
    assert tracked is not eager
