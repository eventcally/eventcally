from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from project.application import commands
from project.application.command_handlers.report_event_handler import ReportEventHandler
from project.application.read_models.access_helper_read_models import (
    MailRecipientReadModel,
)
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from tests.unit.application.conftest import ACTOR, FakeEmailService


class _FakeAccessRepo:
    def __init__(self):
        self.calls = []

    def event_report_recipients(self, admin_unit_id, permission):
        self.calls.append((admin_unit_id, permission))
        return [MailRecipientReadModel(id=1, email="admin@test.de", locale="de")]


def _make_event(uow, admin_unit_id=3):
    event = EventAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Reported Event",
        organizer_id=1,
        event_place_id=1,
        date_definitions=[
            EventDateDefinitionValueObject(start=datetime.now(ZoneInfo("UTC")))
        ],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )
    uow.events.add(event)
    return event


def _cmd(event_id):
    return commands.ReportEventCommand.model_construct(
        actor=ACTOR,
        event_id=event_id,
        contact_name="Firstname Lastname",
        contact_email="first@test.de",
        message="Diese Veranstaltung wird nicht stattfinden.",
    )


class TestReportEventHandler:
    def test_mails_recipients_with_report(self, uow):
        event = _make_event(uow, admin_unit_id=3)
        repo = _FakeAccessRepo()
        email_service = FakeEmailService()

        ReportEventHandler(repo, email_service).handle(_cmd(event.id), uow)

        assert repo.calls == [(3, "events:write")]
        assert len(email_service.calls) == 1
        call = email_service.calls[0]
        assert [u.email for u in call["users"]] == ["admin@test.de"]
        assert call["template"] == "event_report_notice"
        assert call["context"]["event"] is event
        assert call["context"]["report"] == {
            "contact_name": "Firstname Lastname",
            "contact_email": "first@test.de",
            "message": "Diese Veranstaltung wird nicht stattfinden.",
        }

    def test_unknown_event_raises_and_sends_nothing(self, uow):
        email_service = FakeEmailService()

        with pytest.raises(NotFoundError):
            ReportEventHandler(_FakeAccessRepo(), email_service).handle(_cmd(999), uow)

        assert email_service.calls == []
