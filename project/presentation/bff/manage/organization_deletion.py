from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, url_for
from flask_babel import gettext

from project.application.commands import (
    CancelOrganizationDeletionCommand,
    RequestOrganizationDeletionCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import GetOrganizationSettingsQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageNameConfirm,
    OrganizationDeletionAnswer,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.shared.utils import strings_are_equal_ignoring_case


def _organization_or_forbidden(id: int, query_bus: QueryBus):
    if not has_access(SimpleNamespace(id=id), "settings:write"):
        raise UnauthorizedError()

    return result_or_404(query_bus.handle(GetOrganizationSettingsQuery(id=id)))


def _check_name(name: str, organization):
    if not strings_are_equal_ignoring_case(name, organization.name):
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match organization name")
        )


def _done(id: int) -> OrganizationDeletionAnswer:
    # Like before no message: the organization page is shown again.
    return OrganizationDeletionAnswer(
        redirect_url=url_for("main.manage_admin_unit", id=id)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/deletion",
    method="POST",
    body=ManageNameConfirm,
    response=OrganizationDeletionAnswer,
    summary="Request the deletion of an organization after typing its name",
)
@inject
def request_organization_deletion(
    id: int,
    body: ManageNameConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization_or_forbidden(id, query_bus)

    if organization.deletion_requested_at:
        abort(400, gettext("Error"))

    _check_name(body.name, organization)
    message_bus.handle_command(RequestOrganizationDeletionCommand(actor=actor(), id=id))

    return _done(id)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/deletion/cancel",
    method="POST",
    body=ManageNameConfirm,
    response=OrganizationDeletionAnswer,
    summary="Cancel the deletion of an organization after typing its name",
)
@inject
def cancel_organization_deletion(
    id: int,
    body: ManageNameConfirm,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization_or_forbidden(id, query_bus)

    if not organization.deletion_requested_at:
        abort(400, gettext("Error"))

    _check_name(body.name, organization)
    message_bus.handle_command(CancelOrganizationDeletionCommand(actor=actor(), id=id))

    return _done(id)
