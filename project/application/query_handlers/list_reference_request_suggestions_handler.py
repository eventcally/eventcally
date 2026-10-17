from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_models.reference_request_suggestions_read_model import (
    ReferenceRequestSuggestionsReadModel,
)
from project.application.read_repositories.abstract_reference_request_suggestion_read_repository import (
    AbstractReferenceRequestSuggestionReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "outgoing_event_reference_requests:write"


class ListReferenceRequestSuggestionsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractReferenceRequestSuggestionReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListReferenceRequestSuggestionsQuery):
        if not self.authz.has_permission_for_admin_unit(
            query.actor, query.admin_unit_id, _PERMISSION
        ):
            return ReferenceRequestSuggestionsReadModel()

        ids = []
        choices = []
        selected_ids = []

        def add(organizations, selected=True):
            for organization in organizations:
                if organization.id in ids:
                    continue
                ids.append(organization.id)
                choices.append(organization)
                if selected:
                    selected_ids.append(organization.id)

        # The sources run in this order and each fills only the remaining slots.
        sources = [
            (self.repo.newest_requested_organizations, True),
            (self.repo.newest_referencing_organizations, True),
            (self.repo.related_organizations, True),
            (self.repo.other_organizations, False),
        ]
        for source, selected in sources:
            limit = query.max_choices - len(ids)
            if limit <= 0:
                break
            add(source(query.admin_unit_id, limit), selected)

        return ReferenceRequestSuggestionsReadModel(
            choices=choices, selected_ids=selected_ids
        )
