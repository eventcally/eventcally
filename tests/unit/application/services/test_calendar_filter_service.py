import pytest

from project.application.read_models.calendar_read_models import CalendarFilterInfo
from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.calendar_filter_service import CalendarFilterService
from project.domain.errors import NotFoundError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader

INFOS = {
    1: CalendarFilterInfo(id=1, admin_unit_id=5, private=False),
    2: CalendarFilterInfo(id=2, admin_unit_id=5, private=True),
}


class FakeRepo(AbstractCalendarReadRepository):
    def organization_exists(self, admin_unit_id):  # pragma: no cover
        return True

    def list(self, query, include_private):  # pragma: no cover
        return None

    def get(self, object_id):  # pragma: no cover
        return None

    def get_filter_infos(self, ids):
        return [INFOS[i] for i in ids if i in INFOS]

    def event_admin_unit_id(self, event_id):  # pragma: no cover
        return None

    def list_calendar_ids_of_event(self, admin_unit_id, event_id):  # pragma: no cover
        return []

    def list_public_calendars_of_other_organizations(
        self, event_id, admin_unit_id
    ):  # pragma: no cover
        return []

    def lookup_public(self, keyword, limit):  # pragma: no cover
        return []

    def is_name_taken(self, admin_unit_id, name, exclude_id=None):  # pragma: no cover
        return False


def _service(**reader):
    return CalendarFilterService(
        FakeRepo(), ActorAuthorizationService(FakeReader(**reader))
    )


ACTOR = Actor(user_id=7)


def test_empty_list_is_allowed_without_lookup():
    _service().ensure_can_filter(None, [])


def test_public_calendar_is_allowed_for_everybody():
    _service().ensure_can_filter(None, [1])


def test_private_calendar_is_allowed_with_read_permission():
    _service(members=[(5, 7, "calendars:read")]).ensure_can_filter(ACTOR, [1, 2])


@pytest.mark.parametrize("actor", [None, ACTOR])
def test_private_calendar_is_hidden_without_read_permission(actor):
    with pytest.raises(NotFoundError):
        _service().ensure_can_filter(actor, [2])


def test_unknown_calendar_answers_the_same():
    with pytest.raises(NotFoundError):
        _service().ensure_can_filter(ACTOR, [1, 99])
