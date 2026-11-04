from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import url_for
from flask_babel import gettext

from project.application.commands import UpdateOrganizationWidgetSettingsCommand
from project.application.message_bus import MessageBus
from project.application.queries import GetOrganizationSettingsQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageMessage,
    WidgetSettingsForm,
    WidgetSettingsSave,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.shared.utils import (
    widget_default_background_color,
    widget_default_primary_color,
)


def _settings_or_forbidden(id: int, query_bus: QueryBus):
    if not has_access(SimpleNamespace(id=id), "widgets:write"):
        raise UnauthorizedError()

    return result_or_404(query_bus.handle(GetOrganizationSettingsQuery(id=id)))


def _stored_color(color, default: str) -> str | None:
    """The default colors are not stored (they follow the defaults of the widget)."""
    return None if not color or color == default else color


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/widget-settings",
    response=WidgetSettingsForm,
    summary="Get the widget colors and the embed instructions of an organization",
)
@inject
def get_widget_settings(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    settings = _settings_or_forbidden(id, query_bus)

    return WidgetSettingsForm(
        id=settings.id,
        font=settings.widget_font or "",
        background_color=settings.widget_background_color
        or widget_default_background_color,
        primary_color=settings.widget_primary_color or widget_default_primary_color,
        link_color=settings.widget_link_color or widget_default_primary_color,
        loader_url=url_for("static", filename="widget-loader.js", _external=True),
        iframe_url=url_for("main.widget_event_dates", id=settings.id, _external=True),
        preview_url=url_for("main.widget_event_dates", id=settings.id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/widget-settings",
    method="PUT",
    body=WidgetSettingsSave,
    response=ManageMessage,
    summary="Save the widget colors of an organization",
)
@inject
def update_widget_settings(
    id: int,
    body: WidgetSettingsSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _settings_or_forbidden(id, query_bus)
    message_bus.handle_command(
        UpdateOrganizationWidgetSettingsCommand(
            actor=actor(),
            id=id,
            widget_font=body.font,
            widget_background_color=_stored_color(
                body.background_color, widget_default_background_color
            ),
            widget_primary_color=_stored_color(
                body.primary_color, widget_default_primary_color
            ),
            # The old form compared the link color with the default primary color.
            widget_link_color=_stored_color(
                body.link_color, widget_default_primary_color
            ),
        )
    )

    return ManageMessage(message=gettext("Settings successfully updated"))
