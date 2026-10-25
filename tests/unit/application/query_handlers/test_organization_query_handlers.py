"""Public organization query handlers — fake repository."""

from project.application import queries
from project.application.query_handlers import (
    GetOrganizationHandler,
    ListVerifierOrganizationsHandler,
    SearchOrganizationsHandler,
)
from project.application.read_models.organization_read_models import (
    OrganizationDetailReadModel,
    OrganizationListItemReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_read_repository import (
    AbstractOrganizationReadRepository,
)


class FakeRepo(AbstractOrganizationReadRepository):
    def __init__(self):
        self.queries = []

    def search(self, query):
        self.queries.append(query)
        item = OrganizationListItemReadModel(id=1, name="Crew")
        return Page(items=[item], page=1, per_page=20, total=1)

    def get_widget_settings(self, object_id):  # pragma: no cover
        return None

    def list_verifiers(self, query):
        self.queries.append(query)
        return Page(items=[], page=1, per_page=20, total=0)

    def get(self, object_id):
        return (
            OrganizationDetailReadModel(id=1, name="Crew") if object_id == 1 else None
        )


def test_search_and_get_are_public():
    repo = FakeRepo()
    query = queries.SearchOrganizationsQuery(keyword="crew", postal_codes=["386"])

    assert SearchOrganizationsHandler(repo).handle(query).total == 1
    assert repo.queries == [query]
    assert (
        GetOrganizationHandler(repo).handle(queries.GetOrganizationQuery(id=1)).name
        == "Crew"
    )
    assert (
        GetOrganizationHandler(repo).handle(queries.GetOrganizationQuery(id=2)) is None
    )


def test_list_verifiers_is_public():
    repo = FakeRepo()
    query = queries.ListVerifierOrganizationsQuery(postal_code="38640")

    result = ListVerifierOrganizationsHandler(repo).handle(query)

    assert result.total == 0
    assert repo.queries == [query]
