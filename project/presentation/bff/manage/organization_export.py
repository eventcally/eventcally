from dependency_injector.wiring import Provide, inject
from flask import current_app, url_for

from project.application.commands import StartOrganizationExportCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetOrganizationExportJobStatusQuery,
    GetOrganizationExportQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    OrganizationExport,
    OrganizationExportFile,
    OrganizationExportJob,
    OrganizationExportJobStatus,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.query_results import result_or_404


def _actor():
    return current_app.container.context.context_provider().current_actor


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/export",
    response=OrganizationExport,
    summary="Get the export file of an organization",
)
@inject
def get_organization_export(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    export = query_bus.handle(
        GetOrganizationExportQuery(actor=_actor(), admin_unit_id=id)
    )

    if export.file is None:
        return OrganizationExport()

    return OrganizationExport(
        file=OrganizationExportFile(
            url=url_for(
                "main.manage_admin_unit_export_dump_files",
                id=id,
                path=f"org-{id}.zip",
            ),
            size=export.file.size,
            created_at=export.file.created_at,
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/export",
    method="POST",
    response=OrganizationExportJob,
    summary="Start the export of an organization",
)
@inject
def start_organization_export(
    id: int, message_bus: MessageBus = Provide[Application.cqrs.message_bus]
):
    result = message_bus.handle_command(
        StartOrganizationExportCommand(actor=_actor(), admin_unit_id=id)
    )
    return OrganizationExportJob(job_id=result.job_id)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/export/jobs/<job_id>",
    response=OrganizationExportJobStatus,
    summary="Get the status of an export job",
)
@inject
def get_organization_export_job_status(
    id: int,
    job_id: str,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    status = result_or_404(
        query_bus.handle(
            GetOrganizationExportJobStatusQuery(
                actor=_actor(), admin_unit_id=id, job_id=job_id
            )
        )
    )
    return OrganizationExportJobStatus(ready=status.ready, successful=status.successful)
