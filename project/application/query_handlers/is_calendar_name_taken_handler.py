from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)


class IsCalendarNameTakenHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractCalendarReadRepository):
        self.repo = repo

    def handle(self, query: queries.IsCalendarNameTakenQuery):
        return self.repo.is_name_taken(
            query.admin_unit_id, query.name, exclude_id=query.exclude_id
        )
