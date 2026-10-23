from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import current_app

from project.application.commands import (
    CreateCustomWidgetCommand,
    DeleteCustomWidgetCommand,
    UpdateCustomWidgetCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import GetCustomWidgetQuery, ListCustomWidgetsQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    CustomWidgetCreated,
    CustomWidgetForm,
    CustomWidgetListItem,
    CustomWidgetListParams,
    CustomWidgetPage,
    CustomWidgetSave,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _actor():
    return current_app.container.context.context_provider().current_actor


def _widget_or_forbidden(id: int, query_bus: QueryBus, permission: str):
    """The widget query is public (widget loader), so authorize here."""
    widget = result_or_404(query_bus.handle(GetCustomWidgetQuery(id=id)))

    if not has_access(widget.admin_unit, permission):
        raise UnauthorizedError()

    return widget


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/custom-widgets",
    query=CustomWidgetListParams,
    response=CustomWidgetPage,
    summary="List custom widgets of an organization",
)
@inject
def list_custom_widgets(
    id: int,
    query: CustomWidgetListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    page = result_or_404(
        query_bus.handle(
            ListCustomWidgetsQuery(admin_unit_id=id, page=query.to_page_request())
        )
    )

    return CustomWidgetPage(
        items=[
            CustomWidgetListItem(id=w.id, name=w.name, widget_type=w.widget_type)
            for w in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "custom_widgets:write"),
    )


@bff_route(
    bff_manage_bp,
    "/custom-widgets/<int:id>",
    response=CustomWidgetForm,
    summary="Get a custom widget",
)
@inject
def get_custom_widget(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    widget = _widget_or_forbidden(id, query_bus, "custom_widgets:read")
    return CustomWidgetForm(
        id=widget.id,
        organization_id=widget.admin_unit_id,
        widget_type=widget.widget_type,
        name=widget.name,
        settings=widget.settings or {},
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/custom-widgets",
    method="POST",
    body=CustomWidgetSave,
    response=CustomWidgetCreated,
    status=201,
    summary="Create a custom widget",
)
@inject
def create_custom_widget(
    id: int,
    body: CustomWidgetSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    result = message_bus.handle_command(
        CreateCustomWidgetCommand(
            actor=_actor(),
            admin_unit_id=id,
            widget_type=body.widget_type,
            name=body.name,
            settings=body.settings,
        )
    )
    return CustomWidgetCreated(id=result.id)


@bff_route(
    bff_manage_bp,
    "/custom-widgets/<int:id>",
    method="PUT",
    body=CustomWidgetSave,
    summary="Update a custom widget",
)
@inject
def update_custom_widget(
    id: int,
    body: CustomWidgetSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    widget = result_or_404(query_bus.handle(GetCustomWidgetQuery(id=id)))
    message_bus.handle_command(
        UpdateCustomWidgetCommand(
            actor=_actor(),
            id=widget.id,
            widget_type=body.widget_type,
            name=body.name,
            settings=body.settings,
        )
    )


@bff_route(
    bff_manage_bp,
    "/custom-widgets/<int:id>",
    method="DELETE",
    summary="Delete a custom widget",
)
@inject
def delete_custom_widget(
    id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    widget = result_or_404(query_bus.handle(GetCustomWidgetQuery(id=id)))
    message_bus.handle_command(DeleteCustomWidgetCommand(actor=_actor(), id=widget.id))
