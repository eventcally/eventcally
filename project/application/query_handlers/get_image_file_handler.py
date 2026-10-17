from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_image_read_repository import (
    AbstractImageReadRepository,
)


class GetImageFileHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractImageReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetImageFileQuery):
        return self.repo.get_file(query.id)
