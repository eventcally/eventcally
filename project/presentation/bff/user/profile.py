from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext
from flask_login import current_user
from flask_security.utils import get_post_login_redirect

from project.application.commands import (
    AcceptTosCommand,
    CancelUserDeletionCommand,
    RequestUserDeletionCommand,
    UpdateUserGeneralSettingsCommand,
    UpdateUserNotificationSettingsCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetSiteNoticesQuery,
    GetUserProfileQuery,
    ListUserOrganizationMembershipsQuery,
)
from project.application.queries.page_request import MAX_PER_PAGE, PageRequest
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.bff.user import actor, bff_user_bp
from project.presentation.bff.user.schemas import (
    UserAcceptTosForm,
    UserAcceptTosParams,
    UserAcceptTosSave,
    UserDeletionConfirm,
    UserGeneralSettingsSave,
    UserNotificationSettingsSave,
    UserProfile,
    UserRedirect,
)
from project.presentation.shared.query_results import result_or_404
from project.shared.utils import strings_are_equal_ignoring_case


def _profile(query_bus: QueryBus):
    return result_or_404(query_bus.handle(GetUserProfileQuery(user_id=current_user.id)))


def _profile_redirect() -> UserRedirect:
    return UserRedirect(redirect_url=url_for("main.profile"))


def _settings_saved() -> UserRedirect:
    flash(gettext("Settings successfully updated"), "success")
    return _profile_redirect()


def _ensure_email_matches(entered: str, profile):
    if not strings_are_equal_ignoring_case(entered, profile.email):
        raise FieldValidationError(
            ["email"], gettext("Entered email does not match your email")
        )


@bff_route(
    bff_user_bp,
    "/profile",
    response=UserProfile,
    summary="Get the profile of the current user",
)
@inject
def get_profile(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    profile = _profile(query_bus)
    return UserProfile(
        email=profile.email,
        locale=profile.locale,
        newsletter_enabled=profile.newsletter_enabled,
        deletion_requested_at=profile.deletion_requested_at,
    )


@bff_route(
    bff_user_bp,
    "/settings/general",
    method="PUT",
    body=UserGeneralSettingsSave,
    response=UserRedirect,
    summary="Update the general settings of the current user",
)
@inject
def update_general_settings(
    body: UserGeneralSettingsSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    message_bus.handle_command(
        UpdateUserGeneralSettingsCommand(
            actor=actor(), id=current_user.id, locale=body.locale
        )
    )
    return _settings_saved()


@bff_route(
    bff_user_bp,
    "/settings/notifications",
    method="PUT",
    body=UserNotificationSettingsSave,
    response=UserRedirect,
    summary="Update the notification settings of the current user",
)
@inject
def update_notification_settings(
    body: UserNotificationSettingsSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    message_bus.handle_command(
        UpdateUserNotificationSettingsCommand(
            actor=actor(),
            id=current_user.id,
            newsletter_enabled=body.newsletter_enabled,
        )
    )
    return _settings_saved()


@bff_route(
    bff_user_bp,
    "/deletion",
    method="POST",
    body=UserDeletionConfirm,
    response=UserRedirect,
    summary="Request the deletion of the account of the current user",
)
@inject
def request_deletion(
    body: UserDeletionConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    profile = _profile(query_bus)

    if profile.deletion_requested_at:
        abort(400, gettext("Your account is scheduled for deletion."))

    # The cap is the query bus page limit; one admin membership is enough anyway.
    memberships = query_bus.handle(
        ListUserOrganizationMembershipsQuery(
            user_id=current_user.id, page=PageRequest(per_page=MAX_PER_PAGE)
        )
    )
    if any(membership.is_admin for membership in memberships.items):
        abort(
            400,
            gettext(
                "You are administrator of at least one organization. Cancel your membership to delete your account."
            ),
        )

    _ensure_email_matches(body.email, profile)
    message_bus.handle_command(
        RequestUserDeletionCommand(actor=actor(), id=current_user.id)
    )
    return _profile_redirect()


@bff_route(
    bff_user_bp,
    "/deletion/cancel",
    method="POST",
    body=UserDeletionConfirm,
    response=UserRedirect,
    summary="Cancel the deletion of the account of the current user",
)
@inject
def cancel_deletion(
    body: UserDeletionConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    profile = _profile(query_bus)

    if not profile.deletion_requested_at:
        abort(400, gettext("Your account is not scheduled for deletion."))

    _ensure_email_matches(body.email, profile)
    message_bus.handle_command(
        CancelUserDeletionCommand(actor=actor(), id=current_user.id)
    )
    return _profile_redirect()


# Both accept-tos routes answer users who have not accepted the terms yet, so the ToS gate
# of `web/requests.py` exempts their endpoints (`bff.bff_user.<function name>`).


@bff_route(
    bff_user_bp,
    "/accept-tos",
    response=UserAcceptTosForm,
    summary="Get what the terms of service confirmation shows",
)
@inject
def get_accept_tos(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    return UserAcceptTosForm(has_tos=query_bus.handle(GetSiteNoticesQuery()).has_tos)


@bff_route(
    bff_user_bp,
    "/accept-tos",
    method="POST",
    query=UserAcceptTosParams,
    body=UserAcceptTosSave,
    response=UserRedirect,
    summary="Accept the terms of service; the `next` query argument is the target",
)
@inject
def accept_tos(
    query: UserAcceptTosParams,
    body: UserAcceptTosSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    if not _profile(query_bus).tos_accepted_at:
        message_bus.handle_command(AcceptTosCommand(actor=actor(), id=current_user.id))

    return UserRedirect(redirect_url=get_post_login_redirect())
