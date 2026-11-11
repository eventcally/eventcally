"""Calendar query handlers — fake repository."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetCalendarHandler,
    IsCalendarNameTakenHandler,
    ListCalendarsHandler,
    ListEventCalendarIdsHandler,
    ListPublicCalendarsForEventHandler,
    LookupPublicCalendarsHandler,
)
from project.application.read_models.calendar_read_models import (
    CalendarReadModel,
    CalendarRefReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz

ORGANIZATION = OrganizationRefReadModel(id=7, name="Crew")


def _calendar(id, private):
    return CalendarReadModel(
        id=id,
        admin_unit_id=7,
        admin_unit=ORGANIZATION,
        name=f"Calendar {id}",
        private=private,
    )


CALENDARS = {1: _calendar(1, False), 2: _calendar(2, True)}


class FakeRepo(AbstractCalendarReadRepository):
    def __init__(self):
        self.include_private = None

    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def list(self, query, include_private):
        self.include_private = include_private
        return Page(items=[], page=1, per_page=20, total=0)

    def get(self, object_id):
        return CALENDARS.get(object_id)

    def get_filter_infos(self, ids):  # pragma: no cover
        return []

    def event_admin_unit_id(self, event_id):
        return 7 if event_id == 1 else None

    def list_calendar_ids_of_event(self, admin_unit_id, event_id):
        return [4, 5]

    def list_public_calendars_of_other_organizations(self, event_id, admin_unit_id):
        return [
            CalendarRefReadModel(
                id=9,
                name="Other",
                organization=OrganizationRefReadModel(id=8, name="X"),
            )
        ]

    def lookup_public(self, keyword, limit):
        self.lookup = (keyword, limit)
        return []

    def is_name_taken(self, admin_unit_id, name, exclude_id=None):
        return (admin_unit_id, name, exclude_id) == (7, "Taken", 3)


def test_list_includes_private_calendars_with_read_permission():
    repo = FakeRepo()
    query = queries.ListCalendarsQuery(admin_unit_id=7, actor=ACTOR)

    page = ListCalendarsHandler(repo, authz("calendars:read")).handle(query)

    assert page.total == 0
    assert repo.include_private is True


def test_list_hides_private_calendars_without_read_permission():
    repo = FakeRepo()
    query = queries.ListCalendarsQuery(admin_unit_id=7, actor=ACTOR)

    ListCalendarsHandler(repo, authz()).handle(query)
    assert repo.include_private is False

    ListCalendarsHandler(repo, authz("calendars:read")).handle(
        queries.ListCalendarsQuery(admin_unit_id=7)
    )
    assert repo.include_private is False


def test_list_unknown_organization_answers_none():
    query = queries.ListCalendarsQuery(admin_unit_id=8, actor=ACTOR)

    assert (
        ListCalendarsHandler(FakeRepo(), authz("calendars:read")).handle(query) is None
    )


def test_get_public_calendar_is_visible_to_everybody():
    handler = GetCalendarHandler(FakeRepo(), authz())

    assert handler.handle(queries.GetCalendarQuery(id=1)).id == 1


def test_get_private_calendar_needs_read_permission():
    query = queries.GetCalendarQuery(id=2, actor=ACTOR)

    assert GetCalendarHandler(FakeRepo(), authz("calendars:read")).handle(query).id == 2
    assert GetCalendarHandler(FakeRepo(), authz()).handle(query) is None
    assert (
        GetCalendarHandler(FakeRepo(), authz()).handle(queries.GetCalendarQuery(id=2))
        is None
    )


def test_get_unknown_calendar_answers_none():
    assert (
        GetCalendarHandler(FakeRepo(), authz()).handle(queries.GetCalendarQuery(id=9))
        is None
    )


def test_is_name_taken_delegates():
    handler = IsCalendarNameTakenHandler(FakeRepo())

    assert handler.handle(
        queries.IsCalendarNameTakenQuery(admin_unit_id=7, name="Taken", exclude_id=3)
    )
    assert not handler.handle(
        queries.IsCalendarNameTakenQuery(admin_unit_id=7, name="Free")
    )


def test_event_calendar_ids_need_read_permission():
    query = queries.ListEventCalendarIdsQuery(admin_unit_id=7, event_id=1, actor=ACTOR)

    assert ListEventCalendarIdsHandler(FakeRepo(), authz("calendars:read")).handle(
        query
    ) == [4, 5]
    with pytest.raises(UnauthorizedError):
        ListEventCalendarIdsHandler(FakeRepo(), authz()).handle(query)


def test_public_calendars_for_event_are_for_event_editors_only():
    query = queries.ListPublicCalendarsForEventQuery(event_id=1, actor=ACTOR)

    calendars = ListPublicCalendarsForEventHandler(
        FakeRepo(), authz("events:read")
    ).handle(query)
    assert [c.id for c in calendars] == [9]
    assert ListPublicCalendarsForEventHandler(FakeRepo(), authz()).handle(query) == []
    assert (
        ListPublicCalendarsForEventHandler(FakeRepo(), authz("events:read")).handle(
            queries.ListPublicCalendarsForEventQuery(event_id=2, actor=ACTOR)
        )
        == []
    )


def test_lookup_public_calendars_strips_the_keyword():
    repo = FakeRepo()

    assert (
        LookupPublicCalendarsHandler(repo).handle(
            queries.LookupPublicCalendarsQuery(keyword="  Sport ", limit=5)
        )
        == []
    )
    assert repo.lookup == ("Sport", 5)
