from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import RequestEventReferenceCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetEventDetailQuery,
    GetManageableOrganizationQuery,
    GetOrganizationQuery,
    PageRequest,
    SearchOrganizationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.events import LOOKUP_PER_PAGE
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    EventReferenceRequestCreate,
    EventReferenceRequestForm,
    EventReferenceRequestSaved,
    ManageRef,
    ManageRefList,
    ManageRefParams,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import can_request_event_reference, has_access
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.reference_request import (
    get_success_text_for_request_creation,
)


def _event_or_error(id: int, event_id: int, query_bus: QueryBus):
    if not has_access(
        SimpleNamespace(id=id), "outgoing_event_reference_requests:write"
    ):
        raise UnauthorizedError()

    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))

    # Do not reveal the events of other organizations.
    if event.admin_unit_id != id:
        abort(404)

    if not can_request_event_reference(event):
        raise UnauthorizedError()

    return event


def _list_url(id: int) -> str:
    return url_for("manage_admin_unit.outgoing_event_reference_requests", id=id)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/reference-request-form",
    response=EventReferenceRequestForm,
    summary="Get the form to request a reference of an event",
)
@inject
def get_event_reference_request_form(
    id: int,
    event_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    event = _event_or_error(id, event_id, query_bus)
    return EventReferenceRequestForm(
        event=ManageRef(id=event.id, name=event.name), list_url=_list_url(id)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/reference-request-organizations",
    query=ManageRefParams,
    response=ManageRefList,
    summary="Look up the organizations that can be asked to reference an event",
)
@inject
def lookup_reference_request_organizations(
    id: int,
    event_id: int,
    query: ManageRefParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _event_or_error(id, event_id, query_bus)
    organization = result_or_404(
        query_bus.handle(GetManageableOrganizationQuery(id=id))
    )
    page = query_bus.handle(
        SearchOrganizationsQuery(
            keyword=query.keyword,
            include_unverified=organization.can_verify_other,
            reference_request_for_admin_unit_id=id,
            page=PageRequest(page=1, per_page=LOOKUP_PER_PAGE),
        )
    )
    return ManageRefList(items=[ManageRef(id=o.id, name=o.name) for o in page.items])


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/reference-requests",
    method="POST",
    body=EventReferenceRequestCreate,
    response=EventReferenceRequestSaved,
    status=201,
    summary="Request a reference of an event from another organization",
)
@inject
def create_event_reference_request(
    id: int,
    event_id: int,
    body: EventReferenceRequestCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _event_or_error(id, event_id, query_bus)

    if body.admin_unit_id is None:
        raise FieldValidationError(
            ["admin_unit_id"], gettext("This field is required.")
        )

    target = result_or_404(
        query_bus.handle(GetOrganizationQuery(id=body.admin_unit_id))
    )
    result = message_bus.handle_command(
        RequestEventReferenceCommand(
            actor=actor(), admin_unit_id=target.id, event_id=event_id
        )
    )

    flash(
        get_success_text_for_request_creation(target.name, result.verified), "success"
    )
    return EventReferenceRequestSaved(
        id=result.id, verified=result.verified, redirect_url=_list_url(id)
    )
