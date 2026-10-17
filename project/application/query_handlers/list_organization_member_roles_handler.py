from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_member_read_repository import (
    AbstractOrganizationMemberReadRepository,
)


class ListOrganizationMemberRolesHandler(AbstractQueryHandler):
    """Role names and titles are not private."""

    def __init__(self, repo: AbstractOrganizationMemberReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListOrganizationMemberRolesQuery):
        return self.repo.list_roles()
