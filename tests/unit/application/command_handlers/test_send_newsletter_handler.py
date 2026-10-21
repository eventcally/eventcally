import pytest
from pydantic import ValidationError

from project.application import commands
from project.application.command_handlers.send_newsletter_handler import (
    SendNewsletterHandler,
)
from project.application.read_models.user_admin_read_models import (
    NewsletterRecipientReadModel,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor
from tests.unit.application.conftest import ACTOR, ACTOR_USER_ID, FakeEmailService


class _FakeUserAdminRepo:
    def __init__(self, recipients):
        self.recipients = recipients

    def list_newsletter_recipients(self):
        return self.recipients


def _make_admin(uow):
    uow.users.add(
        UserAggregate(
            id=ACTOR_USER_ID, email="admin@test.de", locale=None, is_platform_admin=True
        )
    )


def _recipients(n):
    return [NewsletterRecipientReadModel(id=i, email=f"u{i}@test.de") for i in range(n)]


def _handler(email_service, recipients=()):
    return SendNewsletterHandler(
        email_service, _FakeUserAdminRepo(list(recipients)), "Site"
    )


def _cmd(**kwargs):
    values = dict(actor=ACTOR, audience="test", test_recipient="t@test.de")
    values.update(kwargs)
    return commands.SendNewsletterCommand.model_construct(message="<p>Hi</p>", **values)


class TestSendNewsletterHandler:
    def test_test_audience_mails_the_recipient(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService()

        result = _handler(email_service, _recipients(3)).handle(_cmd(), uow)

        assert (result.job_id, result.count) == ("job-1", 1)
        call = email_service.calls[0]
        assert call["email"] == "t@test.de"
        assert call["template"] == "newsletter"
        assert call["context"] == {"site_name": "Site", "message": "<p>Hi</p>"}

    def test_all_audience_mails_every_recipient(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService()

        result = _handler(email_service, _recipients(3)).handle(
            _cmd(audience="all", test_recipient=None), uow
        )

        assert (result.job_id, result.count) == ("job-1", 3)
        assert len(email_service.calls[0]["users"]) == 3

    def test_all_audience_without_recipients_is_empty(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService()

        result = _handler(email_service).handle(
            _cmd(audience="all", test_recipient=None), uow
        )

        assert (result.job_id, result.count) == (None, 0)
        assert email_service.calls == []

    def test_non_admin_is_unauthorized(self, uow):
        email_service = FakeEmailService()

        with pytest.raises(UnauthorizedError):
            _handler(email_service, _recipients(3)).handle(
                _cmd(audience="all", test_recipient=None), uow
            )

        assert email_service.calls == []


class TestSendNewsletterCommand:
    def test_test_without_recipient_is_invalid(self):
        with pytest.raises(ValidationError):
            commands.SendNewsletterCommand(actor=Actor(), audience="test", message="Hi")

    def test_all_with_recipient_is_invalid(self):
        with pytest.raises(ValidationError):
            commands.SendNewsletterCommand(
                actor=Actor(), audience="all", test_recipient="t@test.de", message="Hi"
            )

    def test_empty_message_is_invalid(self):
        with pytest.raises(ValidationError):
            commands.SendNewsletterCommand(actor=Actor(), audience="all", message="")

    def test_valid_commands(self):
        commands.SendNewsletterCommand(actor=Actor(), audience="all", message="Hi")
        commands.SendNewsletterCommand(
            actor=Actor(), audience="test", test_recipient="t@test.de", message="Hi"
        )
