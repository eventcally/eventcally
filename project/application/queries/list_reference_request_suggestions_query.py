from project.application.queries.base import Query
from project.application.read_models.reference_request_suggestions_read_model import (
    ReferenceRequestSuggestionsReadModel,
)
from project.domain.types.object_id import ObjectId


class ListReferenceRequestSuggestionsQuery(Query[ReferenceRequestSuggestionsReadModel]):
    """Organizations to suggest as reference request targets for the events of
    `admin_unit_id`. Requires `outgoing_event_reference_requests:write`; without it the
    suggestions are empty."""

    admin_unit_id: ObjectId
    max_choices: int = 5
