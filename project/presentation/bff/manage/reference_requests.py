from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort
from flask_babel import gettext

from project.application.queries import (
    GetOutgoingEventReferenceRequestQuery,
    ListIncomingEventReferenceRequestsQuery,
    ListOutgoingEventReferenceRequestsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    EventReferenceRequestListItem,
    EventReferenceRequestListPage,
    EventReferenceRequestListParams,
    ManageAudit,
    ManageIntChoice,
    OutgoingEventReferenceRequestRead,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.shared.utils import get_localized_enum_name


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _review_status_choices() -> list[ManageIntChoice]:
    # The order and the "All" option of the old filter.
    return [ManageIntChoice(value=-1, label=gettext("All"))] + [
        ManageIntChoice(value=int(status), label=str(get_localized_enum_name(status)))
        for status in EventReferenceRequestReviewStatus
    ]


def _review_status_or_none(value):
    try:
        return EventReferenceRequestReviewStatus(int(value))
    except (TypeError, ValueError):
        return None


def _list_page(page, can_write, organization, can_review) -> dict:
    return dict(
        items=[
            EventReferenceRequestListItem(
                id=r.id,
                event_id=r.event.id,
                event_name=r.event.name,
                organization_id=organization(r).id,
                organization_name=organization(r).name,
                review_status=int(r.review_status),
                review_status_label=str(get_localized_enum_name(r.review_status)),
                created_at=r.created_at,
                can_review=can_review(r),
            )
            for r in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=can_write,
        review_status_choices=_review_status_choices(),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-reference-requests",
    query=EventReferenceRequestListParams,
    response=EventReferenceRequestListPage,
    summary="List the reference requests to an organization",
)
@inject
def list_incoming_event_reference_requests(
    id: int,
    query: EventReferenceRequestListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "incoming_event_reference_requests:read")
    page = result_or_404(
        query_bus.handle(
            ListIncomingEventReferenceRequestsQuery(
                admin_unit_id=id,
                review_status=_review_status_or_none(query.review_status),
                page=query.to_page_request(),
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    can_write = has_access(
        SimpleNamespace(id=id), "incoming_event_reference_requests:write"
    )

    return EventReferenceRequestListPage(
        **_list_page(
            page,
            can_write,
            # The organization of the requested event.
            lambda r: r.event.admin_unit,
            lambda r: can_write
            and r.review_status != EventReferenceRequestReviewStatus.verified,
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-event-reference-requests",
    query=EventReferenceRequestListParams,
    response=EventReferenceRequestListPage,
    summary="List the reference requests of an organization's events",
)
@inject
def list_outgoing_event_reference_requests(
    id: int,
    query: EventReferenceRequestListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "outgoing_event_reference_requests:read")
    page = result_or_404(
        query_bus.handle(
            ListOutgoingEventReferenceRequestsQuery(
                admin_unit_id=id,
                review_status=_review_status_or_none(query.review_status),
                page=query.to_page_request(),
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return EventReferenceRequestListPage(
        **_list_page(page, False, lambda r: r.admin_unit, lambda r: False)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-event-reference-requests/<int:request_id>",
    response=OutgoingEventReferenceRequestRead,
    summary="Get an outgoing event reference request",
)
@inject
def get_outgoing_event_reference_request(
    id: int,
    request_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "outgoing_event_reference_requests:read")
    request = result_or_404(
        query_bus.handle(GetOutgoingEventReferenceRequestQuery(id=request_id))
    )

    # Do not reveal the requests of other organizations.
    if request.event.admin_unit.id != id:
        abort(404)

    return OutgoingEventReferenceRequestRead(
        id=request.id,
        event_id=request.event.id,
        event_name=request.event.name,
        review_status=int(request.review_status),
        review_status_label=str(get_localized_enum_name(request.review_status)),
        rejection_reason_label=(
            str(get_localized_enum_name(request.rejection_reason))
            if request.rejection_reason
            else None
        ),
        organization_id=request.admin_unit.id,
        organization_name=request.admin_unit.name,
        audit=ManageAudit(**request.audit.model_dump()) if request.audit else None,
    )
