from dependency_injector.wiring import Provide, inject
from flask import current_app

from project.application.commands import (
    CreateEventReferenceCommand,
    DeleteEventReferenceCommand,
)
from project.application.message_bus import MessageBus
from project.container import Application
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    EventReferenceCreate,
    EventReferenceCreated,
)
from project.presentation.bff.routing import bff_route


def _actor():
    return current_app.container.context.context_provider().current_actor


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-references",
    method="POST",
    body=EventReferenceCreate,
    response=EventReferenceCreated,
    status=201,
    summary="Reference an event",
)
@inject
def create_event_reference(
    id: int,
    body: EventReferenceCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    result = message_bus.handle_command(
        CreateEventReferenceCommand(
            actor=_actor(), admin_unit_id=id, event_id=body.event_id
        )
    )
    return EventReferenceCreated(id=result.id)


@bff_route(
    bff_manage_bp,
    "/event-references/<int:id>",
    method="DELETE",
    summary="Delete an event reference",
)
@inject
def delete_event_reference(
    id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    message_bus.handle_command(DeleteEventReferenceCommand(actor=_actor(), id=id))
