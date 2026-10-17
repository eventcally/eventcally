"""Batch and image query handlers — pass-through to the repositories."""

from project.application import queries
from project.application import query_handlers as handlers
from project.application.read_repositories.abstract_batch_read_repository import (
    AbstractBatchReadRepository,
)
from project.application.read_repositories.abstract_image_read_repository import (
    AbstractImageReadRepository,
)


class FakeBatchRepo(AbstractBatchReadRepository):
    def __init__(self):
        self.calls = []

    def _record(self, name, *args):
        self.calls.append((name, *args))
        return name

    def list_dump_events(self, query):
        return self._record("events", query)

    def list_dump_places(self, query):
        return self._record("places", query)

    def list_dump_organizers(self, query):
        return self._record("organizers", query)

    def list_dump_organizations(self, query):
        return self._record("organizations", query)

    def list_dump_event_categories(self):
        return self._record("categories")

    def list_dump_event_references(self, query):
        return self._record("references", query)

    def list_sitemap_events(self):
        return self._record("sitemap")

    def list_organization_ids_due_for_deletion(self):
        return self._record("orgs")

    def list_user_ids_due_for_deletion(self):
        return self._record("users")

    def list_ghost_user_ids(self):
        return self._record("ghosts")

    def list_old_event_ids(self):
        return self._record("old_events")

    def list_recurring_event_ids(self):
        return self._record("recurring_events")


class FakeImageRepo(AbstractImageReadRepository):
    def get_meta(self, image_id):
        return ("meta", image_id)

    def get_file(self, image_id):
        return ("file", image_id)


def test_batch_handlers_pass_queries_through():
    repo = FakeBatchRepo()
    cases = [
        (handlers.ListDumpEventsHandler, queries.ListDumpEventsQuery(), "events"),
        (handlers.ListDumpPlacesHandler, queries.ListDumpPlacesQuery(), "places"),
        (
            handlers.ListDumpOrganizersHandler,
            queries.ListDumpOrganizersQuery(),
            "organizers",
        ),
        (
            handlers.ListDumpOrganizationsHandler,
            queries.ListDumpOrganizationsQuery(),
            "organizations",
        ),
        (
            handlers.ListDumpEventCategoriesHandler,
            queries.ListDumpEventCategoriesQuery(),
            "categories",
        ),
        (
            handlers.ListDumpEventReferencesHandler,
            queries.ListDumpEventReferencesQuery(),
            "references",
        ),
        (
            handlers.ListSitemapEventsHandler,
            queries.ListSitemapEventsQuery(),
            "sitemap",
        ),
        (
            handlers.ListOrganizationIdsDueForDeletionHandler,
            queries.ListOrganizationIdsDueForDeletionQuery(),
            "orgs",
        ),
        (
            handlers.ListUserIdsDueForDeletionHandler,
            queries.ListUserIdsDueForDeletionQuery(),
            "users",
        ),
        (handlers.ListGhostUserIdsHandler, queries.ListGhostUserIdsQuery(), "ghosts"),
        (handlers.ListOldEventIdsHandler, queries.ListOldEventIdsQuery(), "old_events"),
        (
            handlers.ListRecurringEventIdsHandler,
            queries.ListRecurringEventIdsQuery(),
            "recurring_events",
        ),
    ]

    for handler_class, query, expected in cases:
        assert handler_class(repo).handle(query) == expected


def test_image_handlers():
    repo = FakeImageRepo()

    assert handlers.GetImageMetaHandler(repo).handle(
        queries.GetImageMetaQuery(id=3)
    ) == (
        "meta",
        3,
    )
    assert handlers.GetImageFileHandler(repo).handle(
        queries.GetImageFileQuery(id=3)
    ) == (
        "file",
        3,
    )
