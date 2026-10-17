"""Event organizer query handlers — fake read repository, no database."""

from project.application import queries
from project.application.query_handlers import (
    GetEventOrganizerForEditHandler,
    GetEventOrganizerHandler,
    GetEventOrganizerRefHandler,
    IsEventOrganizerNameTakenHandler,
    ListEventOrganizersHandler,
    LookupEventOrganizersHandler,
)
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerDetailReadModel,
    EventOrganizerEditReadModel,
    EventOrganizerListItemReadModel,
    EventOrganizerRefReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_organizer_read_repository import (
    AbstractEventOrganizerReadRepository,
)


class FakeEventOrganizerReadRepository(AbstractEventOrganizerReadRepository):
    def __init__(self, organization_ids=(), details=(), taken=(), edits=()):
        self.edits = {edit.id: edit for edit in edits}
        self.organization_ids = set(organization_ids)
        self.details = {detail.id: detail for detail in details}
        self.taken = set(taken)
        self.list_queries = []
        self.lookup_queries = []
        self.refs = {(7, 3): EventOrganizerRefReadModel(id=3, name="Crew")}

    def lookup(self, query):
        self.lookup_queries.append(query)
        return Page[EventOrganizerRefReadModel](
            items=[EventOrganizerRefReadModel(id=1, name="Organizer")],
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
        return Page[EventOrganizerListItemReadModel](
            items=[EventOrganizerListItemReadModel(id=1, name="Organizer")],
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
            and organizer_id != exclude_id
            for organization_id, taken_name, organizer_id in self.taken
        )


class TestListEventOrganizersHandler:
    def test_returns_page_from_repository(self):
        repo = FakeEventOrganizerReadRepository(organization_ids=[7])
        query = queries.ListEventOrganizersQuery(admin_unit_id=7, keyword="crew")

        page = ListEventOrganizersHandler(repo).handle(query)

        assert [item.name for item in page.items] == ["Organizer"]
        assert repo.list_queries == [query]

    def test_unknown_organization_returns_none(self):
        repo = FakeEventOrganizerReadRepository(organization_ids=[7])
        query = queries.ListEventOrganizersQuery(admin_unit_id=8)

        assert ListEventOrganizersHandler(repo).handle(query) is None
        assert repo.list_queries == []


class TestGetEventOrganizerHandler:
    def test_returns_detail(self):
        detail = EventOrganizerDetailReadModel(
            id=3,
            name="Organizer",
            admin_unit=OrganizationRefReadModel(id=7, name="Crew"),
        )
        repo = FakeEventOrganizerReadRepository(details=[detail])

        result = GetEventOrganizerHandler(repo).handle(
            queries.GetEventOrganizerQuery(id=3)
        )

        assert result is detail

    def test_unknown_organizer_returns_none(self):
        repo = FakeEventOrganizerReadRepository()

        result = GetEventOrganizerHandler(repo).handle(
            queries.GetEventOrganizerQuery(id=3)
        )

        assert result is None


class TestIsEventOrganizerNameTakenHandler:
    def _handle(self, **kwargs):
        repo = FakeEventOrganizerReadRepository(taken=[(7, "Crew", 3)])
        query = queries.IsEventOrganizerNameTakenQuery(**kwargs)
        return IsEventOrganizerNameTakenHandler(repo).handle(query)

    def test_taken(self):
        assert self._handle(admin_unit_id=7, name="crew") is True

    def test_free(self):
        assert self._handle(admin_unit_id=7, name="Other") is False

    def test_own_name_is_not_taken(self):
        assert self._handle(admin_unit_id=7, name="Crew", exclude_id=3) is False


class TestGetEventOrganizerForEditHandler:
    def test_returns_edit_model(self):
        edit = EventOrganizerEditReadModel(id=3, admin_unit_id=7, name="Name")
        repo = FakeEventOrganizerReadRepository(edits=[edit])

        result = GetEventOrganizerForEditHandler(repo).handle(
            queries.GetEventOrganizerForEditQuery.model_construct(id=3)
        )

        assert result == edit

    def test_unknown_returns_none(self):
        repo = FakeEventOrganizerReadRepository()

        result = GetEventOrganizerForEditHandler(repo).handle(
            queries.GetEventOrganizerForEditQuery.model_construct(id=3)
        )

        assert result is None


class TestEventOrganizerLookupHandlers:
    def test_lookup_passes_the_query_to_the_repository(self):
        repo = FakeEventOrganizerReadRepository()
        query = queries.LookupEventOrganizersQuery(admin_unit_id=7, term="cr")

        page = LookupEventOrganizersHandler(repo).handle(query)

        assert repo.lookup_queries == [query]
        assert [item.name for item in page.items] == ["Organizer"]

    def test_get_ref_is_scoped_to_the_organization(self):
        handler = GetEventOrganizerRefHandler(FakeEventOrganizerReadRepository())

        found = handler.handle(queries.GetEventOrganizerRefQuery(admin_unit_id=7, id=3))
        other = handler.handle(queries.GetEventOrganizerRefQuery(admin_unit_id=8, id=3))

        assert found.name == "Crew"
        assert other is None
