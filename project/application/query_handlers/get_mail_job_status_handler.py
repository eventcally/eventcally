from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.services.abstract_mail_job_status_reader import (
    AbstractMailJobStatusReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetMailJobStatusHandler(AbstractQueryHandler):
    def __init__(
        self, reader: AbstractMailJobStatusReader, authz: ActorAuthorizationService
    ):
        self.reader = reader
        self.authz = authz

    def handle(self, query: queries.GetMailJobStatusQuery):
        self.authz.ensure_is_platform_admin(query.actor)
        return self.reader.get(query.job_id)
