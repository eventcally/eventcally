"""ListExternalCalendarEventsHandler — fake reader and settings, no database."""

import json
from datetime import date

import pytest

from project.application import queries
from project.application.query_handlers import ListExternalCalendarEventsHandler
from project.application.read_models.external_calendar_read_models import (
    ExternalCalendarEventReadModel,
)
from project.application.read_models.settings_read_model import SettingsReadModel
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)
from project.application.services.abstract_external_calendar_reader import (
    AbstractExternalCalendarReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_actor_permission_policy import (
    FakeActorPermissionReader,
)

URL = "https://example.com/holidays.ics"
PLANNER = Actor(user_id=7)


class FakePermissionReader(FakeActorPermissionReader):
    def is_member_of_verified_organization(self, user_id):
        return False


class FakeSettingsRepo(AbstractSiteSettingsReadRepository):
    def __init__(self, calendars):
        self.calendars = calendars

    def get_site_notices(self):  # pragma: no cover
        raise NotImplementedError

    def get_settings(self):
        return SettingsReadModel(planning_external_calendars=self.calendars)


class FakeReader(AbstractExternalCalendarReader):
    def __init__(self):
        self.calls = []

    def list_events(self, url, start, end):
        self.calls.append((url, start, end))
        return [
            ExternalCalendarEventReadModel(name="Holiday", start=start, allday=True)
        ]


def _handler(calendars, reader=None):
    return ListExternalCalendarEventsHandler(
        FakeSettingsRepo(calendars),
        reader or FakeReader(),
        ActorAuthorizationService(FakePermissionReader(admins=[7])),
    )


def _query(actor=PLANNER, url=URL):
    return queries.ListExternalCalendarEventsQuery(
        url=url, date_from=date(2026, 10, 1), date_to=date(2026, 10, 31), actor=actor
    )


def test_configured_url_is_passed_to_the_reader():
    reader = FakeReader()
    handler = _handler(json.dumps([{"title": "H", "url": URL}]), reader)

    result = handler.handle(_query())

    assert reader.calls == [(URL, date(2026, 10, 1), date(2026, 10, 31))]
    assert result[0].name == "Holiday"


def test_actor_who_cannot_plan_is_refused():
    handler = _handler(json.dumps([{"url": URL}]))

    with pytest.raises(UnauthorizedError):
        handler.handle(_query(actor=Actor(user_id=8)))

    with pytest.raises(UnauthorizedError):
        handler.handle(_query(actor=None))


def test_unknown_url_is_refused():
    reader = FakeReader()
    handler = _handler(json.dumps([{"url": URL}]), reader)

    with pytest.raises(UnauthorizedError):
        handler.handle(_query(url="https://evil.example.com/x.ics"))

    assert reader.calls == []


@pytest.mark.parametrize("calendars", [None, "", "not json", "[{}]", "[1]", '{"a":1}'])
def test_missing_or_invalid_settings_refuse_every_url(calendars):
    with pytest.raises(UnauthorizedError):
        _handler(calendars).handle(_query())
