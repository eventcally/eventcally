"""Unit tests for UserDeletionRequestedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.user_deletion_requested_email_event_handler import (  # noqa: E501
    UserDeletionRequestedEmailEventHandler,
)
from project.domain import events
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor


class TestUserDeletionRequestedEmailEventHandler:
    def _seed_user(self, uow, email="user@test.de"):
        user = UserAggregate(id=-1, email=email, locale=None)
        uow.users.add(user)
        return user

    def test_sends_email_when_user_found(self, uow):
        user = self._seed_user(uow)
        email_service = MagicMock()

        ev = events.UserDeletionRequested(actor=Actor(), id=user.id)
        UserDeletionRequestedEmailEventHandler(email_service=email_service).handle(
            ev, uow
        )

        email_service.send_template_mails_to_users_async.assert_called_once_with(
            [user],
            "user_deletion_requested_notice",
            user=user,
        )

    def test_user_not_found_does_not_crash(self, uow):
        email_service = MagicMock()

        ev = events.UserDeletionRequested(actor=Actor(), id=999)
        UserDeletionRequestedEmailEventHandler(email_service=email_service).handle(
            ev, uow
        )

        email_service.send_template_mails_to_users_async.assert_not_called()
