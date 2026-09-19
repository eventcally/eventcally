"""Unit tests for UpdateUserGeneralSettingsHandler and UpdateUserNotificationSettingsHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.update_user_general_settings_handler import (
    UpdateUserGeneralSettingsHandler,
)
from project.application.command_handlers.update_user_notification_settings_handler import (  # noqa: E501
    UpdateUserNotificationSettingsHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID


def _make_user(uow, id=ACTOR_USER_ID, **kwargs):
    user = UserAggregate(id=id, email="user@test.de", locale=None, **kwargs)
    uow.users.add(user)
    return user


class TestUpdateUserGeneralSettingsHandler:
    def test_updates_locale(self, uow):
        _make_user(uow)
        cmd = commands.UpdateUserGeneralSettingsCommand.model_construct(
            actor=ACTOR, id=ACTOR_USER_ID, locale="de"
        )

        UpdateUserGeneralSettingsHandler().handle(cmd, uow)

        updated = uow.users.get(ACTOR_USER_ID)
        assert updated.locale == "de"

    def test_updates_locale_to_none(self, uow):
        user = _make_user(uow)
        user.update(actor=ACTOR, locale="de")
        uow.users.update(user)

        cmd = commands.UpdateUserGeneralSettingsCommand.model_construct(
            actor=ACTOR, id=ACTOR_USER_ID, locale=None
        )

        UpdateUserGeneralSettingsHandler().handle(cmd, uow)

        updated = uow.users.get(ACTOR_USER_ID)
        assert updated.locale is None

    def test_not_found_raises(self, uow):
        cmd = commands.UpdateUserGeneralSettingsCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            UpdateUserGeneralSettingsHandler().handle(cmd, uow)

    def test_other_actor_raises_unauthorized_error(self, uow):
        _make_user(uow, id=999)
        cmd = commands.UpdateUserGeneralSettingsCommand.model_construct(
            actor=ACTOR, id=999
        )

        with pytest.raises(UnauthorizedError):
            UpdateUserGeneralSettingsHandler().handle(cmd, uow)


class TestUpdateUserNotificationSettingsHandler:
    def test_updates_newsletter_enabled(self, uow):
        _make_user(uow)
        cmd = commands.UpdateUserNotificationSettingsCommand.model_construct(
            actor=ACTOR, id=ACTOR_USER_ID, newsletter_enabled=False
        )

        UpdateUserNotificationSettingsHandler().handle(cmd, uow)

        updated = uow.users.get(ACTOR_USER_ID)
        assert updated.newsletter_enabled is False

    def test_not_found_raises(self, uow):
        cmd = commands.UpdateUserNotificationSettingsCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            UpdateUserNotificationSettingsHandler().handle(cmd, uow)

    def test_other_actor_raises_unauthorized_error(self, uow):
        _make_user(uow, id=999)
        cmd = commands.UpdateUserNotificationSettingsCommand.model_construct(
            actor=ACTOR, id=999
        )

        with pytest.raises(UnauthorizedError):
            UpdateUserNotificationSettingsHandler().handle(cmd, uow)
