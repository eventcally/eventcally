from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, current_app, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateEventReferenceCommand,
    DeleteEventReferenceCommand,
    UpdateEventReferenceCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetIncomingEventReferenceQuery,
    ListIncomingEventReferencesQuery,
    ListOutgoingEventReferencesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    EventReferenceCreate,
    EventReferenceCreated,
    EventReferenceListItem,
    IncomingEventReferenceListPage,
    IncomingEventReferenceRating,
    IncomingEventReferenceRead,
    ManageAudit,
    ManageDeleted,
    ManageDeleteSave,
    ManageIntChoice,
    ManageMessage,
    ManagePagedListParams,
    OutgoingEventReferenceListPage,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.event_rating import event_rating_choices
from project.presentation.shared.query_results import result_or_404


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


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _rating_choices() -> list[ManageIntChoice]:
    return [
        ManageIntChoice(value=value, label=str(label))
        for value, label in event_rating_choices
    ]


def _list_item(reference, organization) -> EventReferenceListItem:
    return EventReferenceListItem(
        id=reference.id,
        event_id=reference.event.id,
        event_name=reference.event.name,
        organization_id=organization.id,
        organization_name=organization.name,
        rating=reference.rating,
        created_at=reference.created_at,
    )


def _reference_or_404(id: int, reference_id: int, query_bus: QueryBus):
    _access_or_forbidden(id, "incoming_event_references:read")
    reference = result_or_404(
        query_bus.handle(GetIncomingEventReferenceQuery(id=reference_id))
    )

    # Do not reveal the references of other organizations.
    if reference.admin_unit_id != id:
        abort(404)

    return reference


def _model_name() -> str:
    return gettext("Incoming reference")


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-references",
    query=ManagePagedListParams,
    response=IncomingEventReferenceListPage,
    summary="List the references other organizations' events got from this organization",
)
@inject
def list_incoming_event_references(
    id: int,
    query: ManagePagedListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "incoming_event_references:read")
    page = result_or_404(
        query_bus.handle(
            ListIncomingEventReferencesQuery(
                admin_unit_id=id, page=query.to_page_request()
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return IncomingEventReferenceListPage(
        items=[_list_item(r, r.event.admin_unit) for r in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "incoming_event_references:write"),
        rating_choices=_rating_choices(),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-event-references",
    query=ManagePagedListParams,
    response=OutgoingEventReferenceListPage,
    summary="List the references of this organization's events",
)
@inject
def list_outgoing_event_references(
    id: int,
    query: ManagePagedListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "outgoing_event_references:read")
    page = result_or_404(
        query_bus.handle(
            ListOutgoingEventReferencesQuery(
                admin_unit_id=id, page=query.to_page_request()
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return OutgoingEventReferenceListPage(
        items=[_list_item(r, r.admin_unit) for r in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=False,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-references/<int:reference_id>",
    response=IncomingEventReferenceRead,
    summary="Get an incoming event reference",
)
@inject
def get_incoming_event_reference(
    id: int,
    reference_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    reference = _reference_or_404(id, reference_id, query_bus)

    return IncomingEventReferenceRead(
        id=reference.id,
        event_id=reference.event.id,
        event_name=reference.event.name,
        rating=reference.rating,
        # As the old read page: no text for a rating of 0.
        rating_text="%d/10" % (reference.rating / 10) if reference.rating else None,
        rating_choices=_rating_choices(),
        audit=ManageAudit(**reference.audit.model_dump()) if reference.audit else None,
        can_write=has_access(SimpleNamespace(id=id), "incoming_event_references:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-references/<int:reference_id>",
    method="PUT",
    body=IncomingEventReferenceRating,
    response=ManageMessage,
    summary="Update the rating of an incoming event reference",
)
@inject
def update_incoming_event_reference(
    id: int,
    reference_id: int,
    body: IncomingEventReferenceRating,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "incoming_event_references:write")
    _reference_or_404(id, reference_id, query_bus)
    message_bus.handle_command(
        UpdateEventReferenceCommand(actor=_actor(), id=reference_id, rating=body.rating)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-references/<int:reference_id>/delete",
    method="POST",
    body=ManageDeleteSave,
    response=ManageDeleted,
    summary="Delete an incoming event reference",
)
@inject
def delete_incoming_event_reference(
    id: int,
    reference_id: int,
    body: ManageDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "incoming_event_references:write")
    _reference_or_404(id, reference_id, query_bus)
    message_bus.handle_command(
        DeleteEventReferenceCommand(actor=_actor(), id=reference_id)
    )
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=_model_name(),
    )

    if not body.inline:
        flash(message, "success")

    return ManageDeleted(
        message=message,
        redirect_url=url_for("manage_admin_unit.incoming_event_references", id=id),
    )
