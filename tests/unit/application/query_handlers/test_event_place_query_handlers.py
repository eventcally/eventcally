"""Event place query handlers — fake read repository, no database."""

from project.application import queries
from project.application.query_handlers import (
    GetEventPlaceForEditHandler,
    GetEventPlaceHandler,
    GetEventPlaceRefHandler,
    IsEventPlaceNameTakenHandler,
    ListEventPlacesHandler,
    ListEventPlaceSuggestionsHandler,
    LookupEventPlacesHandler,
)
from project.application.read_models.event_place_read_models import (
    EventPlaceDetailReadModel,
    EventPlaceEditReadModel,
    EventPlaceListItemReadModel,
    EventPlaceSuggestionReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)


class FakeEventPlaceReadRepository(AbstractEventPlaceReadRepository):
    def __init__(self, organization_ids=(), details=(), taken=(), edits=()):
        self.edits = {edit.id: edit for edit in edits}
        self.organization_ids = set(organization_ids)
        self.details = {detail.id: detail for detail in details}
        self.taken = set(taken)
        self.list_queries = []
        self.suggestion_queries = []
        self.lookup_queries = []
        self.refs = {(7, 3): EventPlaceSuggestionReadModel(id=3, name="Halle")}

    def lookup(self, query):
        self.lookup_queries.append(query)
        return Page[EventPlaceSuggestionReadModel](
            items=[EventPlaceSuggestionReadModel(id=1, name="Place")],
            page=query.page.page,
            per_page=query.page.per_page,
            total=1,
        )

    def get_ref(self, admin_unit_id, object_id):
        return self.refs.get((admin_unit_id, object_id))

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organization_ids

    def list(self, query):
        self.list_queries.append(query)
        return Page[EventPlaceListItemReadModel](
            items=[EventPlaceListItemReadModel(id=1, name="Place")],
            page=query.page.page,
            per_page=query.page.per_page,
            total=1,
        )

    def get(self, object_id):
        return self.details.get(object_id)

    def get_for_edit(self, object_id):
        return self.edits.get(object_id)

    def is_name_taken(self, admin_unit_id, name, exclude_id=None):
        return any(
            organization_id == admin_unit_id
            and taken_name.lower() == name.lower()
            and place_id != exclude_id
            for organization_id, taken_name, place_id in self.taken
        )

    def list_suggestions(self, query):
        self.suggestion_queries.append(query)
        return [EventPlaceSuggestionReadModel(id=1, name="Place")]


class TestListEventPlacesHandler:
    def test_returns_page_from_repository(self):
        repo = FakeEventPlaceReadRepository(organization_ids=[7])
        query = queries.ListEventPlacesQuery(admin_unit_id=7, keyword="halle")

        page = ListEventPlacesHandler(repo).handle(query)

        assert [item.name for item in page.items] == ["Place"]
        assert repo.list_queries == [query]

    def test_unknown_organization_returns_none(self):
        repo = FakeEventPlaceReadRepository(organization_ids=[7])
        query = queries.ListEventPlacesQuery(admin_unit_id=8)

        assert ListEventPlacesHandler(repo).handle(query) is None
        assert repo.list_queries == []


class TestGetEventPlaceHandler:
    def test_returns_detail(self):
        detail = EventPlaceDetailReadModel(
            id=3,
            name="Place",
            admin_unit=OrganizationRefReadModel(id=7, name="Crew"),
        )
        repo = FakeEventPlaceReadRepository(details=[detail])

        result = GetEventPlaceHandler(repo).handle(queries.GetEventPlaceQuery(id=3))

        assert result is detail

    def test_unknown_place_returns_none(self):
        repo = FakeEventPlaceReadRepository()

        result = GetEventPlaceHandler(repo).handle(queries.GetEventPlaceQuery(id=3))

        assert result is None


class TestIsEventPlaceNameTakenHandler:
    def _handle(self, **kwargs):
        repo = FakeEventPlaceReadRepository(taken=[(7, "Halle", 3)])
        query = queries.IsEventPlaceNameTakenQuery(**kwargs)
        return IsEventPlaceNameTakenHandler(repo).handle(query)

    def test_taken(self):
        assert self._handle(admin_unit_id=7, name="halle") is True

    def test_free(self):
        assert self._handle(admin_unit_id=7, name="Other") is False

    def test_own_name_is_not_taken(self):
        assert self._handle(admin_unit_id=7, name="Halle", exclude_id=3) is False


class TestListEventPlaceSuggestionsHandler:
    def test_passes_query_through_without_organization_check(self):
        repo = FakeEventPlaceReadRepository()
        query = queries.ListEventPlaceSuggestionsQuery(admin_unit_id=9, keyword="ha")

        result = ListEventPlaceSuggestionsHandler(repo).handle(query)

        assert [item.name for item in result] == ["Place"]
        assert repo.suggestion_queries == [query]


class TestGetEventPlaceForEditHandler:
    def test_returns_edit_model(self):
        edit = EventPlaceEditReadModel(id=3, admin_unit_id=7, name="Name")
        repo = FakeEventPlaceReadRepository(edits=[edit])

        result = GetEventPlaceForEditHandler(repo).handle(
            queries.GetEventPlaceForEditQuery.model_construct(id=3)
        )

        assert result == edit

    def test_unknown_returns_none(self):
        repo = FakeEventPlaceReadRepository()

        result = GetEventPlaceForEditHandler(repo).handle(
            queries.GetEventPlaceForEditQuery.model_construct(id=3)
        )

        assert result is None


class TestEventPlaceLookupHandlers:
    def test_lookup_passes_the_query_to_the_repository(self):
        repo = FakeEventPlaceReadRepository()
        query = queries.LookupEventPlacesQuery(admin_unit_id=7, term="ha")

        page = LookupEventPlacesHandler(repo).handle(query)

        assert repo.lookup_queries == [query]
        assert [item.name for item in page.items] == ["Place"]

    def test_get_ref_is_scoped_to_the_organization(self):
        handler = GetEventPlaceRefHandler(FakeEventPlaceReadRepository())

        found = handler.handle(queries.GetEventPlaceRefQuery(admin_unit_id=7, id=3))
        other = handler.handle(queries.GetEventPlaceRefQuery(admin_unit_id=8, id=3))

        assert found.name == "Halle"
        assert other is None
