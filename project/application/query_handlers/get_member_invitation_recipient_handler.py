from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_member_invitation_read_repository import (
    AbstractOrganizationMemberInvitationReadRepository,
)


class GetMemberInvitationRecipientHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractOrganizationMemberInvitationReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetMemberInvitationRecipientQuery):
        return self.repo.get_recipient_email(query.id)
