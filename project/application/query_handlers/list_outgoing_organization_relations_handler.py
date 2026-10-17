from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_relation_read_repository import (
    AbstractOrganizationRelationReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "outgoing_organization_relations:read"


class ListOutgoingOrganizationRelationsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationRelationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListOutgoingOrganizationRelationsQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, _PERMISSION
        )
        return self.repo.list(query)
