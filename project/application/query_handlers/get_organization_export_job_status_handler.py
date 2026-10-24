from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.services.abstract_organization_export_reader import (
    AbstractOrganizationExportReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.organization_export_jobs import (
    is_organization_export_job_id,
)


class GetOrganizationExportJobStatusHandler(AbstractQueryHandler):
    def __init__(
        self,
        reader: AbstractOrganizationExportReader,
        authz: ActorAuthorizationService,
    ):
        self.reader = reader
        self.authz = authz

    def handle(self, query: queries.GetOrganizationExportJobStatusQuery):
        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, "export:read"
        )

        if not is_organization_export_job_id(query.admin_unit_id, query.job_id):
            return None

        return self.reader.get_job_status(query.job_id)
