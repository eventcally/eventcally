"""Unit tests for ReferenceEventChangedEmailEventHandler."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from project.application.event_handlers.reference_event_changed_email_event_handler import (
    ReferenceEventChangedEmailEventHandler,
)
from project.application.read_models.event_change_summary_read_model import (
    EventChangeSummaryReadModel,
)
from project.application.services.event_change_summary_service import (
    EventChangeSummaryService,
)
from project.domain import events
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types.changed_value import ChangedValue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(uow):
    org = EventOrganizerAggregate.create(actor=Actor(), admin_unit_id=1, name="Org")
    uow.event_organizers.add(org)
    place = EventPlaceAggregate.create(actor=Actor(), admin_unit_id=1, name="Place")
    uow.event_places.add(place)
    event = EventAggregate.create(
        actor=Actor(),
        admin_unit_id=1,
        name="Event",
        organizer_id=org.id,
        event_place_id=place.id,
        date_definitions=[
            EventDateDefinitionValueObject(start=datetime.now(timezone.utc))
        ],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )
    uow.events.add(event)
    return event


class FakeChangeSummaryService(EventChangeSummaryService):
    """Keeps the real (pure) gate, but records and stubs the resolving build()."""

    def __init__(self, summary=None):
        super().__init__(event_read_repo=MagicMock())
        self.summary = summary if summary is not None else EventChangeSummaryReadModel()
        self.build_calls = 0

    def build(self, event):
        self.build_calls += 1
        return self.summary


def _make_handler(email_service, details_enabled=True, summary=None):
    org_service = MagicMock()
    org_service.send_template_mails_to_members_async = MagicMock()
    # Keep a reference via the email_service attribute so tests can inspect
    org_service._email_service = email_service
    event_read_repo = MagicMock()
    event_read_repo.get = MagicMock(return_value=MagicMock())
    change_summary_service = FakeChangeSummaryService(summary)
    return (
        ReferenceEventChangedEmailEventHandler(
            organization_service=org_service,
            event_read_repo=event_read_repo,
            change_summary_service=change_summary_service,
            details_enabled=details_enabled,
        ),
        org_service,
        change_summary_service,
    )


def _make_updated_event(event, **changes):
    return events.EventUpdated(
        actor=Actor(),
        id=event.id,
        admin_unit_id=event.admin_unit_id,
        **changes,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReferenceEventChangedEmailEventHandler:
    def test_no_significant_changes_does_not_send_email(self, uow, email_service):
        event = _make_event(uow)
        handler, org_service, _ = _make_handler(email_service)

        ev = _make_updated_event(event)
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_not_called()

    def test_no_references_for_event_does_not_send_email(self, uow, email_service):
        event = _make_event(uow)
        # No references seeded → get_by_event_id returns []
        handler, org_service, _ = _make_handler(email_service)

        ev = _make_updated_event(event, name=ChangedValue(old="old", new="new"))
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_not_called()

    def test_name_change_with_reference_sends_email(self, uow, email_service):
        event = _make_event(uow)
        # Add a fake reference
        from unittest.mock import MagicMock as _M

        ref = _M()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(event, name=ChangedValue(old="old", new="new"))
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_status_change_sends_email(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(
            event,
            status=ChangedValue(old=EventStatus.scheduled, new=EventStatus.cancelled),
        )
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_attendance_mode_change_sends_email(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(
            event,
            attendance_mode=ChangedValue(
                old=EventAttendanceMode.online, new=EventAttendanceMode.offline
            ),
        )
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_booked_up_change_sends_email(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(event, booked_up=ChangedValue(old=False, new=True))
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_event_place_id_change_sends_email(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(event, event_place_id=ChangedValue(old=1, new=2))
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_organizer_id_change_sends_email(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(event, organizer_id=ChangedValue(old=1, new=2))
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_date_definitions_change_sends_email(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        old_dd = EventDateDefinitionValueObject(
            start=datetime(2020, 1, 1, tzinfo=timezone.utc)
        )
        new_dd = EventDateDefinitionValueObject(
            start=datetime(2021, 1, 1, tzinfo=timezone.utc)
        )
        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(
            event, date_definitions=ChangedValue(old=[old_dd], new=[new_dd])
        )
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()

    def test_multiple_references_sends_email_per_reference(self, uow, email_service):
        event = _make_event(uow)
        ref1 = MagicMock()
        ref1.admin_unit_id = 99
        ref2 = MagicMock()
        ref2.admin_unit_id = 100
        uow.event_references._references_by_event[event.id] = [ref1, ref2]

        handler, org_service, _ = _make_handler(email_service)
        ev = _make_updated_event(event, name=ChangedValue(old="a", new="b"))
        handler.handle(ev, uow)

        assert org_service.send_template_mails_to_members_async.call_count == 2

    def test_summary_is_built_once_for_all_references(self, uow, email_service):
        event = _make_event(uow)
        ref1 = MagicMock()
        ref1.admin_unit_id = 99
        ref2 = MagicMock()
        ref2.admin_unit_id = 100
        uow.event_references._references_by_event[event.id] = [ref1, ref2]

        summary = EventChangeSummaryReadModel(name=ChangedValue(old="a", new="b"))
        handler, org_service, change_summary_service = _make_handler(
            email_service, summary=summary
        )
        ev = _make_updated_event(event, name=ChangedValue(old="a", new="b"))
        handler.handle(ev, uow)

        assert change_summary_service.build_calls == 1
        for call in org_service.send_template_mails_to_members_async.call_args_list:
            assert call.kwargs["changes"] is summary

    def test_details_enabled_passes_summary_to_the_template(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        summary = EventChangeSummaryReadModel(name=ChangedValue(old="a", new="b"))
        handler, org_service, _ = _make_handler(
            email_service, details_enabled=True, summary=summary
        )
        ev = _make_updated_event(event, name=ChangedValue(old="a", new="b"))
        handler.handle(ev, uow)

        call = org_service.send_template_mails_to_members_async.call_args
        assert call.kwargs["changes"] is summary

    def test_details_disabled_sends_mail_without_summary(self, uow, email_service):
        event = _make_event(uow)
        ref = MagicMock()
        ref.admin_unit_id = 99
        uow.event_references._references_by_event[event.id] = [ref]

        handler, org_service, change_summary_service = _make_handler(
            email_service, details_enabled=False
        )
        ev = _make_updated_event(event, name=ChangedValue(old="a", new="b"))
        handler.handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once()
        call = org_service.send_template_mails_to_members_async.call_args
        assert call.kwargs["changes"] is None
        assert change_summary_service.build_calls == 0
