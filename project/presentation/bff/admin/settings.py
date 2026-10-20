import json
from enum import StrEnum
from typing import Optional

from dependency_injector.wiring import Provide, inject
from flask import abort, current_app
from flask_security import auth_required

from project.application.commands import (
    ResetTosAcceptedForUsersCommand,
    UpdatePlanningSettingsCommand,
    UpdateSettingsCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import GetSettingsForAdminQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.admin import bff_admin_bp
from project.presentation.bff.admin.schemas import (
    AdminPlanning,
    AdminPlanningUpdate,
    AdminSettings,
    AdminSettingUpdate,
)
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route


class SettingKey(StrEnum):
    # The values are the field names of `AdminSettings` and `UpdateSettingsCommand`.
    start_page = "start_page"
    tos = "tos"
    legal_notice = "legal_notice"
    contact = "contact"
    privacy = "privacy"
    announcement = "announcement"


def _blank_to_none(value: Optional[str]) -> Optional[str]:
    return None if value is None or not value.strip() else value


@bff_route(
    bff_admin_bp,
    "/settings",
    response=AdminSettings,
    summary="Get settings",
)
@auth_required("session")
@inject
def get_settings(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    settings = query_bus.handle(GetSettingsForAdminQuery())
    return AdminSettings(**settings.model_dump(include=set(AdminSettings.model_fields)))


@bff_route(
    bff_admin_bp,
    "/settings/reset-tos-accepted",
    method="POST",
    summary="Reset terms of service acceptance",
)
@auth_required("session")
@inject
def reset_tos_accepted(
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    message_bus.handle_command(
        ResetTosAcceptedForUsersCommand(
            actor=current_app.container.context.context_provider().current_actor,
        )
    )


@bff_route(
    bff_admin_bp,
    "/settings/<key>",
    method="PUT",
    body=AdminSettingUpdate,
    summary="Update setting",
)
@auth_required("session")
@inject
def update_setting(
    key: str,
    body: AdminSettingUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    try:
        field = SettingKey(key)
    except ValueError:
        abort(404)

    message_bus.handle_command(
        UpdateSettingsCommand(
            actor=current_app.container.context.context_provider().current_actor,
            **{field.value: _blank_to_none(body.value)},
        )
    )


@bff_route(
    bff_admin_bp,
    "/planning",
    response=AdminPlanning,
    summary="Get planning settings",
)
@auth_required("session")
@inject
def get_planning(query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    settings = query_bus.handle(GetSettingsForAdminQuery())
    return AdminPlanning(
        planning_external_calendars=settings.planning_external_calendars
    )


@bff_route(
    bff_admin_bp,
    "/planning",
    method="PUT",
    body=AdminPlanningUpdate,
    response=AdminPlanning,
    summary="Update planning settings",
)
@auth_required("session")
@inject
def update_planning(
    body: AdminPlanningUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    value = _blank_to_none(body.planning_external_calendars)

    if value is not None:
        try:
            value = json.dumps(json.loads(value), indent=2)
        except ValueError as e:
            raise FieldValidationError(["planning_external_calendars"], str(e))

    message_bus.handle_command(
        UpdatePlanningSettingsCommand(
            actor=current_app.container.context.context_provider().current_actor,
            planning_external_calendars=value,
        )
    )

    return AdminPlanning(planning_external_calendars=value)
