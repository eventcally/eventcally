from project.application.services.abstract_organization_export_dispatcher import (
    AbstractOrganizationExportDispatcher,
)
from project.domain.types import ObjectId

# Frozen wire name of `presentation.tasks.celery_tasks.dump_admin_unit_task`; looked up
# instead of imported because infrastructure must not import the presentation layer.
DUMP_TASK_NAME = "project.celery_tasks.dump_admin_unit_task"


class CeleryOrganizationExportDispatcher(AbstractOrganizationExportDispatcher):
    def start(self, admin_unit_id: ObjectId, job_id: str) -> bool:
        from project.infrastructure.celery_app import celery

        celery.tasks[DUMP_TASK_NAME].apply_async(args=[admin_unit_id], task_id=job_id)

        # Eager mode has no result backend: the task already ran, nothing to track.
        return not celery.conf.task_always_eager
