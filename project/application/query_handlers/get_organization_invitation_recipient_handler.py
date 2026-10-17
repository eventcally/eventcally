from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_invitation_read_repository import (
    AbstractOrganizationInvitationReadRepository,
)


class GetOrganizationInvitationRecipientHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractOrganizationInvitationReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetOrganizationInvitationRecipientQuery):
        return self.repo.get_recipient_email(query.id)
