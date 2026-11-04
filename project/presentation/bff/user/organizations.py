from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext
from flask_login import current_user

from project.application.commands import (
    AcceptMemberInvitationCommand,
    DeclineMemberInvitationCommand,
    DeclineOrganizationInvitationCommand,
    LeaveOrganizationCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetUserMemberInvitationQuery,
    GetUserOrganizationInvitationQuery,
    GetUserOrganizationMembershipQuery,
    GetUserProfileQuery,
    ListUserMemberInvitationsQuery,
    ListUserOrganizationInvitationsQuery,
    ListUserOrganizationMembershipsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.bff.user import actor, bff_user_bp
from project.presentation.bff.user.schemas import (
    UserMemberInvitationItem,
    UserMemberInvitationPage,
    UserMembershipDetail,
    UserMembershipItem,
    UserMembershipPage,
    UserNameConfirm,
    UserOrganizationInvitationItem,
    UserOrganizationInvitationPage,
    UserRedirect,
)
from project.presentation.shared.access import can_current_user_delete_member
from project.presentation.shared.query_results import result_or_404
from project.shared.utils import strings_are_equal_ignoring_case


def _redirect(endpoint: str, message: str, category: str = "success", **values):
    flash(message, category)
    return UserRedirect(redirect_url=url_for(endpoint, **values))


# Memberships


@bff_route(
    bff_user_bp,
    "/memberships",
    query=PageParams,
    response=UserMembershipPage,
    summary="List the organizations the current user is a member of",
)
@inject
def list_memberships(
    query: PageParams, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    page = query_bus.handle(
        ListUserOrganizationMembershipsQuery(
            user_id=current_user.id, page=query.to_page_request()
        )
    )

    if page.is_out_of_range:
        abort(404)

    return UserMembershipPage(
        items=[
            UserMembershipItem(
                id=m.id,
                organization_id=m.admin_unit_id,
                organization_name=m.admin_unit.name,
                is_admin=m.is_admin,
            )
            for m in page.items
        ],
        **UserMembershipPage.paging(page),
    )


@bff_route(
    bff_user_bp,
    "/memberships/<int:id>",
    response=UserMembershipDetail,
    summary="Get a membership of the current user",
)
@inject
def get_membership(id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    membership = result_or_404(
        query_bus.handle(GetUserOrganizationMembershipQuery(id=id))
    )
    return UserMembershipDetail(
        id=membership.id,
        organization_id=membership.admin_unit_id,
        organization_name=membership.admin_unit.name,
        can_leave=can_current_user_delete_member(membership),
    )


@bff_route(
    bff_user_bp,
    "/memberships/<int:id>/leave",
    method="POST",
    body=UserNameConfirm,
    response=UserRedirect,
    summary="Leave an organization after typing its name",
)
@inject
def leave_organization(
    id: int,
    body: UserNameConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    membership = result_or_404(
        query_bus.handle(GetUserOrganizationMembershipQuery(id=id))
    )

    if not can_current_user_delete_member(membership):
        abort(
            400, gettext("Last remaining administrator can not leave the organization.")
        )

    if not strings_are_equal_ignoring_case(body.name, membership.admin_unit.name):
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match organization name")
        )

    message_bus.handle_command(LeaveOrganizationCommand(actor=actor(), id=id))
    return _redirect(
        "user.organization_members", gettext("Organization successfully left")
    )


# Member invitations


@bff_route(
    bff_user_bp,
    "/member-invitations",
    query=PageParams,
    response=UserMemberInvitationPage,
    summary="List the invitations to join an organization",
)
@inject
def list_member_invitations(
    query: PageParams, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    page = query_bus.handle(
        ListUserMemberInvitationsQuery(
            user_id=current_user.id, page=query.to_page_request()
        )
    )

    if page.is_out_of_range:
        abort(404)

    return UserMemberInvitationPage(
        items=[
            UserMemberInvitationItem(
                id=i.id,
                organization_id=i.admin_unit_id,
                organization_name=i.admin_unit.name,
            )
            for i in page.items
        ],
        **UserMemberInvitationPage.paging(page),
    )


@bff_route(
    bff_user_bp,
    "/member-invitations/<int:id>",
    response=UserMemberInvitationItem,
    summary="Get an invitation to join an organization",
)
@inject
def get_member_invitation(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    invitation = result_or_404(query_bus.handle(GetUserMemberInvitationQuery(id=id)))
    return UserMemberInvitationItem(
        id=invitation.id,
        organization_id=invitation.admin_unit_id,
        organization_name=invitation.admin_unit.name,
    )


@bff_route(
    bff_user_bp,
    "/member-invitations/<int:id>/accept",
    method="POST",
    response=UserRedirect,
    summary="Accept an invitation to join an organization",
)
@inject
def accept_member_invitation(
    id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    invitation = result_or_404(query_bus.handle(GetUserMemberInvitationQuery(id=id)))
    profile = result_or_404(
        query_bus.handle(GetUserProfileQuery(user_id=current_user.id))
    )

    if profile.deletion_requested_at:
        return _redirect(
            "main.profile", gettext("Your account is scheduled for deletion."), "danger"
        )

    message_bus.handle_command(AcceptMemberInvitationCommand(actor=actor(), id=id))
    return _redirect(
        "main.manage_admin_unit",
        gettext("Invitation successfully accepted"),
        id=invitation.admin_unit_id,
    )


@bff_route(
    bff_user_bp,
    "/member-invitations/<int:id>/decline",
    method="POST",
    response=UserRedirect,
    summary="Decline an invitation to join an organization",
)
@inject
def decline_member_invitation(
    id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    result_or_404(query_bus.handle(GetUserMemberInvitationQuery(id=id)))
    message_bus.handle_command(DeclineMemberInvitationCommand(actor=actor(), id=id))
    return _redirect("main.manage", gettext("Invitation successfully declined"))


# Organization invitations


def _organization_invitation_item(invitation) -> UserOrganizationInvitationItem:
    return UserOrganizationInvitationItem(
        id=invitation.id,
        organization_id=invitation.admin_unit_id,
        organization_name=invitation.admin_unit.name,
        name=invitation.admin_unit_name,
        created_at=invitation.created_at,
    )


@bff_route(
    bff_user_bp,
    "/organization-invitations",
    query=PageParams,
    response=UserOrganizationInvitationPage,
    summary="List the invitations to create an organization",
)
@inject
def list_organization_invitations(
    query: PageParams, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    page = query_bus.handle(
        ListUserOrganizationInvitationsQuery(
            user_id=current_user.id, page=query.to_page_request()
        )
    )

    if page.is_out_of_range:
        abort(404)

    return UserOrganizationInvitationPage(
        items=[_organization_invitation_item(i) for i in page.items],
        **UserOrganizationInvitationPage.paging(page),
    )


@bff_route(
    bff_user_bp,
    "/organization-invitations/<int:id>",
    response=UserOrganizationInvitationItem,
    summary="Get an invitation to create an organization",
)
@inject
def get_organization_invitation(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    return _organization_invitation_item(
        result_or_404(query_bus.handle(GetUserOrganizationInvitationQuery(id=id)))
    )


@bff_route(
    bff_user_bp,
    "/organization-invitations/<int:id>/decline",
    method="POST",
    response=UserRedirect,
    summary="Decline an invitation to create an organization",
)
@inject
def decline_organization_invitation(
    id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    result_or_404(query_bus.handle(GetUserOrganizationInvitationQuery(id=id)))
    message_bus.handle_command(
        DeclineOrganizationInvitationCommand(actor=actor(), id=id)
    )
    return _redirect(
        "user.organization_invitations", gettext("Invitation successfully declined")
    )
