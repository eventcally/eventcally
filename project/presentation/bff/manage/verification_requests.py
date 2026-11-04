from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    RequestOrganizationVerificationCommand,
    WithdrawOrganizationVerificationRequestCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    CanRequestVerificationQuery,
    GetManageableOrganizationQuery,
    GetOrganizationQuery,
    GetOutgoingOrganizationVerificationRequestQuery,
    ListIncomingOrganizationVerificationRequestsQuery,
    ListOutgoingOrganizationVerificationRequestsQuery,
    ListVerifierOrganizationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors import BaseError
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    IncomingVerificationRequestListPage,
    ManageAudit,
    ManageDeleted,
    ManageDeleteSave,
    ManageIntChoice,
    ManageMessage,
    OutgoingVerificationRequestListPage,
    OutgoingVerificationRequestRead,
    VerificationRequestCreate,
    VerificationRequestListItem,
    VerificationRequestListParams,
    VerifierOrganization,
    VerifierOrganizationListPage,
)
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.urls import url_for_image
from project.shared.utils import get_localized_enum_name, get_location_str

# The domain enum is named differently than the ORM enum the msgids are keyed by.
STATUS_ENUM_NAME = "AdminUnitVerificationRequestReviewStatus"
REASON_ENUM_NAME = "AdminUnitVerificationRequestRejectionReason"

INCOMING = "incoming_organization_verification_requests"
OUTGOING = "outgoing_organization_verification_requests"


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _status_label(status) -> str:
    return str(get_localized_enum_name(status, STATUS_ENUM_NAME))


def _review_status_choices() -> list[ManageIntChoice]:
    # The order and the "All" option of the old filter.
    return [ManageIntChoice(value=-1, label=gettext("All"))] + [
        ManageIntChoice(value=int(status), label=_status_label(status))
        for status in OrganizationVerificationRequestReviewStatus
    ]


def _review_status_or_none(value):
    try:
        return OrganizationVerificationRequestReviewStatus(int(value))
    except (TypeError, ValueError):
        return None


def _page_fields(page, can_write: bool) -> dict:
    return dict(
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=can_write,
    )


def _request_or_404(id: int, request_id: int, query_bus: QueryBus):
    _access_or_forbidden(id, f"{OUTGOING}:read")

    # Do not reveal the requests of other organizations: the query refuses them for
    # lack of permission on their requesting organization.
    try:
        request = result_or_404(
            query_bus.handle(
                GetOutgoingOrganizationVerificationRequestQuery(id=request_id)
            )
        )
    except UnauthorizedError:
        abort(404)

    if request.source_admin_unit_id != id:  # pragma: no cover
        abort(404)

    return request


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-verification-requests",
    query=VerificationRequestListParams,
    response=IncomingVerificationRequestListPage,
    summary="List the verification requests to an organization",
)
@inject
def list_incoming_verification_requests(
    id: int,
    query: VerificationRequestListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, f"{INCOMING}:read")
    page = result_or_404(
        query_bus.handle(
            ListIncomingOrganizationVerificationRequestsQuery(
                admin_unit_id=id,
                review_status=_review_status_or_none(query.review_status),
                page=query.to_page_request(),
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    can_write = has_access(SimpleNamespace(id=id), f"{INCOMING}:write")

    return IncomingVerificationRequestListPage(
        items=[
            VerificationRequestListItem(
                id=r.id,
                organization_id=r.source_admin_unit.id,
                organization_name=r.source_admin_unit.name,
                review_status=int(r.review_status),
                review_status_label=_status_label(r.review_status),
                created_at=r.created_at,
                can_review=can_write
                and r.review_status
                != OrganizationVerificationRequestReviewStatus.verified,
            )
            for r in page.items
        ],
        review_status_choices=_review_status_choices(),
        **_page_fields(page, can_write),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-verification-requests",
    query=PageParams,
    response=OutgoingVerificationRequestListPage,
    summary="List the verification requests of an organization",
)
@inject
def list_outgoing_verification_requests(
    id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, f"{OUTGOING}:read")
    organization = result_or_404(
        query_bus.handle(GetManageableOrganizationQuery(id=id))
    )
    page = result_or_404(
        query_bus.handle(
            ListOutgoingOrganizationVerificationRequestsQuery(
                admin_unit_id=id, page=query.to_page_request()
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    can_write = has_access(SimpleNamespace(id=id), f"{OUTGOING}:write")

    return OutgoingVerificationRequestListPage(
        items=[
            VerificationRequestListItem(
                id=r.id,
                organization_id=r.target_admin_unit.id,
                organization_name=r.target_admin_unit.name,
                review_status=int(r.review_status),
                review_status_label=_status_label(r.review_status),
                created_at=r.created_at,
            )
            for r in page.items
        ],
        suggest_create=can_write and not organization.is_verified and page.total == 0,
        **_page_fields(page, can_write),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-verification-requests/<int:request_id>",
    response=OutgoingVerificationRequestRead,
    summary="Get a verification request of an organization",
)
@inject
def get_outgoing_verification_request(
    id: int,
    request_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    request = _request_or_404(id, request_id, query_bus)

    return OutgoingVerificationRequestRead(
        id=request.id,
        organization_id=request.target_admin_unit.id,
        organization_name=request.target_admin_unit.name,
        review_status=int(request.review_status),
        review_status_label=_status_label(request.review_status),
        rejection_reason_label=(
            str(get_localized_enum_name(request.rejection_reason, REASON_ENUM_NAME))
            if request.rejection_reason
            else None
        ),
        audit=ManageAudit(**request.audit.model_dump()) if request.audit else None,
        can_write=has_access(SimpleNamespace(id=id), f"{OUTGOING}:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-verification-requests/<int:request_id>/withdraw",
    method="POST",
    body=ManageDeleteSave,
    response=ManageDeleted,
    summary="Withdraw a verification request",
)
@inject
def withdraw_outgoing_verification_request(
    id: int,
    request_id: int,
    body: ManageDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, f"{OUTGOING}:write")
    _request_or_404(id, request_id, query_bus)
    message_bus.handle_command(
        WithdrawOrganizationVerificationRequestCommand(actor=actor(), id=request_id)
    )

    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=gettext("Organization verification request"),
    )

    # Withdrawn on the read page (which is gone): the list shows the flash.
    if not body.inline:
        flash(message, "success")

    return ManageDeleted(
        message=message,
        redirect_url=url_for(
            "manage_admin_unit.outgoing_organization_verification_requests", id=id
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/verifier-organizations",
    query=PageParams,
    response=VerifierOrganizationListPage,
    summary="List the organizations that can verify an organization",
)
@inject
def list_verifier_organizations(
    id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, f"{OUTGOING}:write")
    organization = result_or_404(
        query_bus.handle(GetManageableOrganizationQuery(id=id))
    )
    postal_code = organization.location.postalCode if organization.location else None
    page = query_bus.handle(
        ListVerifierOrganizationsQuery(
            postal_code=postal_code or "", page=query.to_page_request()
        )
    )

    if page.is_out_of_range:
        abort(404)

    return VerifierOrganizationListPage(
        items=[
            VerifierOrganization(
                id=o.id,
                name=o.name,
                is_verified=o.is_verified,
                location=get_location_str(o.location) or None,
                logo_url=url_for_image(o.logo, s=120) if o.logo else None,
                description=o.description,
                incoming_verification_requests_text=o.incoming_verification_requests_text,
                can_request=query_bus.handle(
                    CanRequestVerificationQuery(
                        source_admin_unit_id=id, target_admin_unit_id=o.id
                    )
                ),
            )
            for o in page.items
        ],
        organization_name=organization.name,
        postal_code=postal_code,
        **_page_fields(page, True),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-verification-requests",
    method="POST",
    body=VerificationRequestCreate,
    response=ManageMessage,
    status=201,
    summary="Ask an organization to verify the organization",
)
@inject
def create_outgoing_verification_request(
    id: int,
    body: VerificationRequestCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, f"{OUTGOING}:write")
    target = result_or_404(query_bus.handle(GetOrganizationQuery(id=body.target_id)))

    if not query_bus.handle(
        CanRequestVerificationQuery(
            source_admin_unit_id=id, target_admin_unit_id=target.id
        )
    ):
        raise BaseError(
            gettext("Verification cannot be requested from this organization.")
        )

    message_bus.handle_command(
        RequestOrganizationVerificationCommand(
            actor=actor(), source_admin_unit_id=id, target_admin_unit_id=target.id
        )
    )

    return ManageMessage(
        message=gettext(
            "Request successfully created. You will be notified after the other organization reviewed the request."
        )
    )
