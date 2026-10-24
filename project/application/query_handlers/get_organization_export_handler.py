from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_models.organization_export_read_models import (
    OrganizationExportReadModel,
)
from project.application.services.abstract_organization_export_reader import (
    AbstractOrganizationExportReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetOrganizationExportHandler(AbstractQueryHandler):
    def __init__(
        self,
        reader: AbstractOrganizationExportReader,
        authz: ActorAuthorizationService,
    ):
        self.reader = reader
        self.authz = authz

    def handle(self, query: queries.GetOrganizationExportQuery):
        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, "export:read"
        )
        return OrganizationExportReadModel(
            file=self.reader.get_file(query.admin_unit_id)
        )
