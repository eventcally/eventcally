"""Event and event-date query handlers — fake repositories, no database."""

from datetime import datetime

import pytest

from project.application import queries
from project.application.query_handlers import (
    EventExistsHandler,
    GetEventDateDetailHandler,
    GetEventDetailHandler,
    GetEventForEditHandler,
    GetIncomingEventReferenceRequestReviewHandler,
    GetOrganizationWidgetSettingsHandler,
    ListAllEventsHandler,
    ListEventDatesHandler,
    ListEventDatesOfEventHandler,
    ListEventsHandler,
    ListUpcomingEventDatesHandler,
    SearchEventDatesHandler,
    SearchEventsHandler,
)
from project.application.read_models.event_read_models import (
    EventDateDetailReadModel,
    EventDateListItemReadModel,
    EventDateReadModel,
    EventDateSearchHitReadModel,
    EventDetailReadModel,
    EventEditReadModel,
    EventListItemReadModel,
    EventOrganizationReadModel,
    EventSearchItemReadModel,
)
from project.application.read_models.event_ref_read_model import EventRefReadModel
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.application.read_models.event_visibility_read_model import (
    EventVisibilityReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)
from project.application.read_repositories.abstract_event_search_read_repository import (
    AbstractEventSearchReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.event_visibility_service import EventVisibilityService
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from tests.application.services.test_event_visibility_service import FakeReader

START = datetime(2040, 1, 1, 10)
ORG = EventOrganizationReadModel(id=2, name="Crew", is_verified=True)


def _item(event_id=1, admin_unit_id=2, internal_tags="secret"):
    return EventSearchItemReadModel(
        id=event_id,
        name=f"Event {event_id}",
        internal_tags=internal_tags,
        admin_unit_id=admin_unit_id,
        organizer_id=1,
        event_place_id=1,
        admin_unit=ORG,
    )


def _detail(event_id=1):
    return EventDetailReadModel(
        **_item(event_id).model_dump(),
        created_by_label="who",
        reference_requests=[],
    )


class FakeSearchRepo(AbstractEventSearchReadRepository):
    def __init__(self, organizations=(2,)):
        self.organizations = set(organizations)
        self.calls = []

    def search_event_dates(self, criteria, page_request, private, planned, reference):
        self.calls.append(("dates", criteria, private, planned, reference))
        hit = EventDateSearchHitReadModel(id=1, start=START, event=_item())
        return Page[EventDateSearchHitReadModel](
            items=[hit], page=1, per_page=20, total=1
        )

    def search_events(
        self, criteria, page_request, private, planned, reference, counts=False
    ):
        self.calls.append(("events", criteria, private, planned, reference))
        return Page[EventSearchItemReadModel](
            items=[_item(1), _item(2, admin_unit_id=3)], page=1, per_page=20, total=2
        )

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organizations

    def list_events(self, query, can_read_private_events):
        self.calls.append(("list", query, can_read_private_events))
        return Page[EventListItemReadModel](items=[], page=1, per_page=20, total=0)

    def list_event_dates(self, query):
        self.calls.append(("list_dates", query))
        return Page[EventDateListItemReadModel](items=[], page=1, per_page=20, total=0)

    def list_events_for_search(self, criteria, private, planned):
        self.calls.append(("all", criteria, private, planned))
        return [_item(1), _item(2, admin_unit_id=3)]


class FakeDetailRepo(AbstractEventDetailReadRepository):
    def __init__(self, status=EventPublicStatus.published, verified=True):
        self.status = status
        self.verified = verified

    def _visibility(self, event_id):
        return EventVisibilityReadModel(
            event_id=event_id,
            public_status=self.status,
            admin_unit_id=2,
            admin_unit_is_verified=self.verified,
        )

    def get_visibility(self, event_id):
        return self._visibility(event_id) if event_id == 1 else None

    def get_visibility_of_date(self, event_date_id):
        return self._visibility(1) if event_date_id == 5 else None

    def get_detail(self, event_id, reference_admin_unit_id):
        return _detail(event_id)

    def get_date_detail(self, event_date_id):
        return EventDateDetailReadModel(id=event_date_id, start=START, event=_detail())

    def list_dates_of_event(self, event_id, page_request):
        return Page[EventDateListItemReadModel](
            items=[EventDateListItemReadModel(id=1, start=START)],
            page=1,
            per_page=20,
            total=1,
        )

    def list_upcoming_dates(self, event_id):
        return [EventDateReadModel(id=1, start=START)]

    def get_for_edit(self, event_id):
        return EventEditReadModel(**_item(event_id).model_dump())


def _visibility(**kwargs):
    return EventVisibilityService(ActorAuthorizationService(FakeReader(**kwargs)))


OWNER = Actor(user_id=7)
MEMBER_READER = dict(members=[(2, 7, "events:read")])


class TestSearchHandlers:
    def test_events_do_not_include_private_ones_without_the_flag(self):
        repo = FakeSearchRepo()
        query = queries.SearchEventsQuery(
            criteria=queries.EventSearchCriteria(admin_unit_id=2), actor=OWNER
        )

        SearchEventsHandler(repo, _visibility(**MEMBER_READER)).handle(query)

        assert repo.calls[0][2:4] == (False, False)

    def test_private_events_are_granted_to_members(self):
        repo = FakeSearchRepo()
        criteria = queries.EventSearchCriteria(admin_unit_id=2, include_private=True)
        query = queries.SearchEventsQuery(
            criteria=criteria, actor=OWNER, reference_admin_unit_id=2
        )

        SearchEventsHandler(repo, _visibility(**MEMBER_READER)).handle(query)

        assert repo.calls[0][2:] == (True, False, 2)

    def test_private_events_are_refused_to_others_and_without_organization(self):
        criteria = queries.EventSearchCriteria(admin_unit_id=2, include_private=True)

        for actor in (None, Actor(user_id=9)):
            repo = FakeSearchRepo()
            SearchEventsHandler(repo, _visibility(**MEMBER_READER)).handle(
                queries.SearchEventsQuery(criteria=criteria, actor=actor)
            )
            assert repo.calls[0][2] is False

        repo = FakeSearchRepo()
        SearchEventsHandler(repo, _visibility(**MEMBER_READER)).handle(
            queries.SearchEventsQuery(
                criteria=queries.EventSearchCriteria(include_private=True),
                actor=OWNER,
            )
        )
        assert repo.calls[0][2] is False

    def test_planners_see_planned_events(self):
        repo = FakeSearchRepo()
        criteria = queries.EventSearchCriteria(include_planned=True)

        SearchEventsHandler(repo, _visibility(verified_members=[7])).handle(
            queries.SearchEventsQuery(criteria=criteria, actor=OWNER)
        )
        SearchEventsHandler(repo, _visibility()).handle(
            queries.SearchEventsQuery(criteria=criteria, actor=OWNER)
        )

        assert [call[3] for call in repo.calls] == [True, False]

    def test_internal_tags_stay_with_the_organizations_members(self):
        repo = FakeSearchRepo()
        page = SearchEventsHandler(repo, _visibility(**MEMBER_READER)).handle(
            queries.SearchEventsQuery(actor=OWNER)
        )

        assert [item.internal_tags for item in page.items] == ["secret", None]

    def test_event_date_hits_redact_the_event(self):
        repo = FakeSearchRepo()
        page = SearchEventDatesHandler(repo, _visibility()).handle(
            queries.SearchEventDatesQuery(actor=OWNER)
        )

        assert page.items[0].event.internal_tags is None
        assert page.total == 1

    def test_all_events_for_a_feed(self):
        repo = FakeSearchRepo()
        events = ListAllEventsHandler(repo, _visibility()).handle(
            queries.ListAllEventsQuery(actor=None)
        )

        assert [e.internal_tags for e in events] == [None, None]
        assert repo.calls[0][2:] == (False, False)


class TestListHandlers:
    def test_unknown_organization_is_none(self):
        repo = FakeSearchRepo()

        result = ListEventsHandler(repo, _visibility()).handle(
            queries.ListEventsQuery(admin_unit_id=4711)
        )

        assert result is None
        assert repo.calls == []

    def test_the_private_right_is_resolved_for_the_organization(self):
        repo = FakeSearchRepo()
        handler = ListEventsHandler(repo, _visibility(**MEMBER_READER))

        handler.handle(
            queries.ListEventsQuery(admin_unit_id=2, include_private=True, actor=OWNER)
        )
        handler.handle(queries.ListEventsQuery(admin_unit_id=2, actor=OWNER))
        handler.handle(queries.ListEventsQuery(include_private=True, actor=OWNER))

        assert [call[2] for call in repo.calls] == [True, False, False]

    def test_public_event_dates_pass_through(self):
        repo = FakeSearchRepo()

        ListEventDatesHandler(repo).handle(queries.ListEventDatesQuery())

        assert repo.calls[0][0] == "list_dates"


class TestDetailHandlers:
    def _handler(self, cls, repo=None, **reader):
        return cls(repo or FakeDetailRepo(), _visibility(**reader))

    def test_public_detail_hides_private_fields_from_strangers(self):
        detail = self._handler(GetEventDetailHandler).handle(
            queries.GetEventDetailQuery(id=1, actor=None)
        )

        assert detail.name == "Event 1"
        assert detail.internal_tags is None
        assert detail.created_by_label is None

    def test_members_see_private_fields(self):
        detail = self._handler(GetEventDetailHandler, **MEMBER_READER).handle(
            queries.GetEventDetailQuery(id=1, actor=OWNER)
        )

        assert detail.internal_tags == "secret"
        assert detail.created_by_label == "who"

    def test_unknown_is_none(self):
        assert (
            self._handler(GetEventDetailHandler).handle(
                queries.GetEventDetailQuery(id=4711)
            )
            is None
        )

    @pytest.mark.parametrize(
        "status, verified",
        [
            (EventPublicStatus.draft, True),
            (EventPublicStatus.planned, True),
            (EventPublicStatus.published, False),
        ],
    )
    def test_unreadable_events_raise(self, status, verified):
        handler = self._handler(
            GetEventDetailHandler, repo=FakeDetailRepo(status, verified)
        )

        with pytest.raises(UnauthorizedError):
            handler.handle(queries.GetEventDetailQuery(id=1, actor=Actor(user_id=9)))

    def test_event_date_detail_authorizes_through_its_event(self):
        repo = FakeDetailRepo(EventPublicStatus.draft)

        with pytest.raises(UnauthorizedError):
            self._handler(GetEventDateDetailHandler, repo=repo).handle(
                queries.GetEventDateDetailQuery(id=5, actor=None)
            )

        detail = self._handler(
            GetEventDateDetailHandler, repo=repo, **MEMBER_READER
        ).handle(queries.GetEventDateDetailQuery(id=5, actor=OWNER))
        assert detail.event.internal_tags == "secret"

        assert (
            self._handler(GetEventDateDetailHandler).handle(
                queries.GetEventDateDetailQuery(id=4711)
            )
            is None
        )

    def test_dates_of_an_event(self):
        handler = self._handler(ListEventDatesOfEventHandler)

        page = handler.handle(queries.ListEventDatesOfEventQuery(event_id=1))
        assert page.total == 1
        assert handler.handle(queries.ListEventDatesOfEventQuery(event_id=4711)) is None

        with pytest.raises(UnauthorizedError):
            self._handler(
                ListEventDatesOfEventHandler,
                repo=FakeDetailRepo(EventPublicStatus.draft),
            ).handle(queries.ListEventDatesOfEventQuery(event_id=1, actor=None))

    def test_upcoming_dates_pass_through(self):
        dates = ListUpcomingEventDatesHandler(FakeDetailRepo()).handle(
            queries.ListUpcomingEventDatesQuery(event_id=1)
        )

        assert [d.id for d in dates] == [1]


def test_widget_settings_pass_through():
    class Repo:
        def get_widget_settings(self, object_id):
            return ("settings", object_id)

    handler = GetOrganizationWidgetSettingsHandler(Repo())

    assert handler.handle(queries.GetOrganizationWidgetSettingsQuery(id=3)) == (
        "settings",
        3,
    )


class TestEditAndExists:
    def test_edit_model_follows_the_visibility_rule(self):
        handler = GetEventForEditHandler(FakeDetailRepo(), _visibility())
        assert handler.handle(queries.GetEventForEditQuery(id=1)).id == 1
        assert handler.handle(queries.GetEventForEditQuery(id=4711)) is None

        with pytest.raises(UnauthorizedError):
            GetEventForEditHandler(
                FakeDetailRepo(EventPublicStatus.draft), _visibility()
            ).handle(queries.GetEventForEditQuery(id=1, actor=Actor(user_id=9)))

    def test_exists_is_unauthorized_knowledge_only(self):
        handler = EventExistsHandler(FakeDetailRepo(EventPublicStatus.draft))

        assert handler.handle(queries.EventExistsQuery(id=1)) is True
        assert handler.handle(queries.EventExistsQuery(id=4711)) is False


class FakeRequestRepo:
    def __init__(self, auto_verify=True):
        self.auto_verify = auto_verify

    def get(self, object_id):
        if object_id != 3:
            return None

        return EventReferenceRequestReadModel(
            id=3,
            admin_unit_id=5,
            event_id=1,
            review_status=EventReferenceRequestReviewStatus.inbox,
            event=EventRefReadModel(
                id=1,
                name="Event 1",
                admin_unit=OrganizationRefReadModel(id=2, name="C"),
            ),
            admin_unit=OrganizationRefReadModel(id=5, name="Reviewer"),
        )

    def auto_verifies(self, source, target):
        return (source, target) == (5, 2) and self.auto_verify


class TestReferenceRequestReview:
    def _handler(self, **reader):
        return GetIncomingEventReferenceRequestReviewHandler(
            FakeRequestRepo(),
            FakeDetailRepo(),
            ActorAuthorizationService(FakeReader(**reader)),
            _visibility(**reader),
        )

    def test_reviewers_get_the_request_with_event_and_dates(self):
        review = self._handler(
            members=[(5, 7, "incoming_event_reference_requests:read")]
        ).handle(queries.GetIncomingEventReferenceRequestReviewQuery(id=3, actor=OWNER))

        assert review.event.name == "Event 1"
        assert review.event.internal_tags is None  # not a member of the event's org
        assert [d.id for d in review.upcoming_dates] == [1]
        assert review.auto_verify is True

    def test_strangers_and_unknown(self):
        with pytest.raises(UnauthorizedError):
            self._handler().handle(
                queries.GetIncomingEventReferenceRequestReviewQuery(id=3, actor=OWNER)
            )

        assert (
            self._handler().handle(
                queries.GetIncomingEventReferenceRequestReviewQuery(id=4711)
            )
            is None
        )
