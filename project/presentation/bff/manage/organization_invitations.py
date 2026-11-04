from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    InviteOrganizationCommand,
    RevokeOrganizationInvitationCommand,
    UpdateOrganizationInvitationCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetManageableOrganizationQuery,
    GetOrganizationInvitationQuery,
    ListOrganizationInvitationsQuery,
    OrganizationInvitationSort,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.types import unset
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageAudit,
    ManageMessage,
    ManagePagedListParams,
    OrganizationInvitationCreate,
    OrganizationInvitationForm,
    OrganizationInvitationListItem,
    OrganizationInvitationListPage,
    OrganizationInvitationSaved,
    OrganizationInvitationUpdate,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _organization(id: int, permission: str, query_bus: QueryBus):
    _access_or_forbidden(id, permission)
    return result_or_404(query_bus.handle(GetManageableOrganizationQuery(id=id)))


def _list_url(id: int) -> str:
    return url_for("manage_admin_unit.organization_invitations", id=id)


def _invitation_or_404(id: int, invitation_id: int, query_bus: QueryBus):
    _access_or_forbidden(id, "organization_invitations:write")

    # Do not reveal the invitations of other organizations: the query refuses them for
    # lack of permission on their organization.
    try:
        invitation = result_or_404(
            query_bus.handle(GetOrganizationInvitationQuery(id=invitation_id))
        )
    except UnauthorizedError:
        abort(404)

    if invitation.admin_unit_id != id:  # pragma: no cover
        abort(404)

    return invitation


def _model_name() -> str:
    return gettext("Organization invitation")


def _saved(id: int, invitation_id: int, text: str) -> OrganizationInvitationSaved:
    flash(text, "success")
    return OrganizationInvitationSaved(id=invitation_id, redirect_url=_list_url(id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/organization-invitations",
    query=ManagePagedListParams,
    response=OrganizationInvitationListPage,
    summary="List the organization invitations of the organization",
)
@inject
def list_organization_invitations(
    id: int,
    query: ManagePagedListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "organization_invitations:read")
    page = result_or_404(
        query_bus.handle(
            ListOrganizationInvitationsQuery(
                admin_unit_id=id,
                sort=OrganizationInvitationSort.created_at_desc,
                page=query.to_page_request(),
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return OrganizationInvitationListPage(
        items=[
            OrganizationInvitationListItem(
                id=i.id,
                email=i.email,
                admin_unit_name=i.admin_unit_name,
                created_at=i.created_at,
            )
            for i in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "organization_invitations:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/organization-invitations/create-form",
    response=OrganizationInvitationForm,
    summary="Get the form to invite an organization",
)
@inject
def get_organization_invitation_create_form(
    id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, "organization_invitations:write", query_bus)

    return OrganizationInvitationForm(
        can_verify_other=organization.can_verify_other, list_url=_list_url(id)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/organization-invitations/<int:invitation_id>",
    response=OrganizationInvitationForm,
    summary="Get the form to update an organization invitation",
)
@inject
def get_organization_invitation_form(
    id: int,
    invitation_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, "organization_invitations:write", query_bus)
    invitation = _invitation_or_404(id, invitation_id, query_bus)

    return OrganizationInvitationForm(
        id=invitation.id,
        email=invitation.email,
        admin_unit_name=invitation.admin_unit_name or "",
        relation_verify=invitation.relation_verify,
        relation_auto_verify_event_reference_requests=(
            invitation.relation_auto_verify_event_reference_requests
        ),
        can_verify_other=organization.can_verify_other,
        audit=(
            ManageAudit(**invitation.audit.model_dump()) if invitation.audit else None
        ),
        list_url=_list_url(id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/organization-invitations",
    method="POST",
    body=OrganizationInvitationCreate,
    response=OrganizationInvitationSaved,
    status=201,
    summary="Invite an organization",
)
@inject
def create_organization_invitation(
    id: int,
    body: OrganizationInvitationCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, "organization_invitations:write", query_bus)
    result = message_bus.handle_command(
        InviteOrganizationCommand(
            actor=actor(),
            admin_unit_id=id,
            email=body.email,
            admin_unit_name=body.admin_unit_name,
            relation_auto_verify_event_reference_requests=(
                body.relation_auto_verify_event_reference_requests
            ),
            # The switch is not offered to an organization that cannot verify others.
            relation_verify=(
                body.relation_verify if organization.can_verify_other else False
            ),
        )
    )

    return _saved(
        id,
        result.id,
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=_model_name(),
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/organization-invitations/<int:invitation_id>",
    method="PUT",
    body=OrganizationInvitationUpdate,
    response=OrganizationInvitationSaved,
    summary="Update an organization invitation",
)
@inject
def update_organization_invitation(
    id: int,
    invitation_id: int,
    body: OrganizationInvitationUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, "organization_invitations:write", query_bus)
    _invitation_or_404(id, invitation_id, query_bus)
    message_bus.handle_command(
        UpdateOrganizationInvitationCommand(
            actor=actor(),
            id=invitation_id,
            admin_unit_name=body.admin_unit_name,
            relation_auto_verify_event_reference_requests=(
                body.relation_auto_verify_event_reference_requests
            ),
            relation_verify=(
                body.relation_verify if organization.can_verify_other else unset
            ),
        )
    )

    return _saved(
        id,
        invitation_id,
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/organization-invitations/<int:invitation_id>/delete",
    method="POST",
    response=ManageMessage,
    summary="Revoke an organization invitation",
)
@inject
def delete_organization_invitation(
    id: int,
    invitation_id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _invitation_or_404(id, invitation_id, query_bus)
    message_bus.handle_command(
        RevokeOrganizationInvitationCommand(actor=actor(), id=invitation_id)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully deleted",
            model_display_name=_model_name(),
        )
    )
