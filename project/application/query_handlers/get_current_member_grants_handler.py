from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_models.access_helper_read_models import (
    MemberGrantsReadModel,
)
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)


class GetCurrentMemberGrantsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAccessReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetCurrentMemberGrantsQuery):
        actor = query.actor

        if actor is None or actor.user_id is None:
            return MemberGrantsReadModel()

        return self.repo.member_grants(query.admin_unit_id, actor.user_id)
