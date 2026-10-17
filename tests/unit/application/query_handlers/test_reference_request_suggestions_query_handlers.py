"""Reference request suggestion handler — fake repository and reader, no database."""

from project.application import queries
from project.application.query_handlers import ListReferenceRequestSuggestionsHandler
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_repositories.abstract_reference_request_suggestion_read_repository import (
    AbstractReferenceRequestSuggestionReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_actor_permission_policy import (
    FakeActorPermissionReader,
)

PERMISSION = "outgoing_event_reference_requests:write"
ACTOR = Actor(user_id=7)


def _org(id):
    return OrganizationRefReadModel(id=id, name=f"Org {id}")


class FakeSuggestionReadRepository(AbstractReferenceRequestSuggestionReadRepository):
    def __init__(self, requested=(), referencing=(), related=(), other=()):
        self.sources = {
            "requested": list(requested),
            "referencing": list(referencing),
            "related": list(related),
            "other": list(other),
        }
        self.limits = {}

    def _take(self, name, limit):
        self.limits[name] = limit
        return [_org(id) for id in self.sources[name]][:limit]

    def newest_requested_organizations(self, admin_unit_id, limit):
        return self._take("requested", limit)

    def newest_referencing_organizations(self, admin_unit_id, limit):
        return self._take("referencing", limit)

    def related_organizations(self, admin_unit_id, limit):
        return self._take("related", limit)

    def other_organizations(self, admin_unit_id, limit):
        return self._take("other", limit)


def _handler(repo, permitted=True):
    members = [(1, 7, PERMISSION)] if permitted else []
    authz = ActorAuthorizationService(FakeActorPermissionReader(members=members))
    return ListReferenceRequestSuggestionsHandler(repo, authz)


def _query(**kwargs):
    return queries.ListReferenceRequestSuggestionsQuery(
        admin_unit_id=1, actor=ACTOR, **kwargs
    )


def test_without_permission_the_suggestions_are_empty_and_nothing_is_read():
    repo = FakeSuggestionReadRepository(requested=[2])

    result = _handler(repo, permitted=False).handle(_query())

    assert result.choices == []
    assert result.selected_ids == []
    assert repo.limits == {}


def test_missing_actor_gets_nothing():
    repo = FakeSuggestionReadRepository(requested=[2])

    result = _handler(repo).handle(
        queries.ListReferenceRequestSuggestionsQuery(admin_unit_id=1)
    )

    assert result.choices == []


def test_sources_are_deduplicated_in_order_and_only_the_last_is_not_selected():
    repo = FakeSuggestionReadRepository(
        requested=[2, 3], referencing=[3, 4], related=[2, 5], other=[6]
    )

    result = _handler(repo).handle(_query(max_choices=6))

    assert [c.id for c in result.choices] == [2, 3, 4, 5, 6]
    assert result.selected_ids == [2, 3, 4, 5]


def test_each_source_only_fills_the_remaining_slots():
    repo = FakeSuggestionReadRepository(
        requested=[2, 3], referencing=[4, 5], related=[6], other=[7]
    )

    result = _handler(repo).handle(_query(max_choices=3))

    assert [c.id for c in result.choices] == [2, 3, 4]
    assert repo.limits == {"requested": 3, "referencing": 1}


def test_default_is_five_choices():
    repo = FakeSuggestionReadRepository(other=range(10, 30))

    result = _handler(repo).handle(_query())

    assert len(result.choices) == 5
    assert result.selected_ids == []
