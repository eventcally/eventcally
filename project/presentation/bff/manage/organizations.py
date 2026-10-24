from types import SimpleNamespace
from typing import Optional

from dependency_injector.wiring import Provide, inject
from flask import flash, url_for
from flask_babel import gettext

from project.application.commands import CreateOrganizationCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    IsOrganizationNameTakenQuery,
    IsOrganizationShortNameTakenQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import (
    actor,
    license_choices,
    location_value_object,
    logo_from_body,
    name_errors,
)
from project.presentation.bff.manage.schemas import (
    OrganizationCreated,
    OrganizationCreateForm,
    OrganizationCreateParams,
    OrganizationCreateRelation,
    OrganizationCreateSave,
    OrganizationNameAvailability,
    OrganizationNameAvailabilityParams,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.organization_create import (
    check_organization_create,
    get_embedded_relation_options,
)
from project.presentation.shared.query_results import result_or_404


def _gate_or_error(invitation_id: Optional[int]):
    gate = check_organization_create(invitation_id)

    if gate.denial == "invitation_missing":
        result_or_404(None)

    if gate.denial:
        raise UnauthorizedError()

    return gate


@bff_route(
    bff_manage_bp,
    "/organizations/name-availability",
    query=OrganizationNameAvailabilityParams,
    response=OrganizationNameAvailability,
    summary="Whether the name and short name of an organization are taken",
)
@inject
def get_organization_name_availability(
    query: OrganizationNameAvailabilityParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    exclude_id = query.exclude_id

    if exclude_id is not None and not has_access(
        SimpleNamespace(id=exclude_id), "settings:write"
    ):
        raise UnauthorizedError()

    result = OrganizationNameAvailability()

    if query.name:
        result.name_taken = query_bus.handle(
            IsOrganizationNameTakenQuery(name=query.name, exclude_id=exclude_id)
        )

    if query.short_name:
        result.short_name_taken = query_bus.handle(
            IsOrganizationShortNameTakenQuery(
                short_name=query.short_name, exclude_id=exclude_id
            )
        )

    return result


@bff_route(
    bff_manage_bp,
    "/organizations/create-form",
    query=OrganizationCreateParams,
    response=OrganizationCreateForm,
    summary="Get the form to create an organization",
)
@inject
def get_organization_create_form(
    query: OrganizationCreateParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    gate = _gate_or_error(query.invitation_id)
    options = get_embedded_relation_options(gate.invitation)

    return OrganizationCreateForm(
        name=gate.invitation.admin_unit_name if gate.invitation else "",
        invitation_id=gate.invitation.id if gate.invitation else None,
        relation=(
            OrganizationCreateRelation(
                organization_name=options.admin_unit.name,
                can_verify=options.can_verify,
                can_auto_verify=options.can_auto_verify,
            )
            if options
            else None
        ),
        licenses=license_choices(query_bus),
    )


@bff_route(
    bff_manage_bp,
    "/organizations",
    method="POST",
    body=OrganizationCreateSave,
    response=OrganizationCreated,
    status=201,
    summary="Create an organization",
)
@inject
def create_organization(
    body: OrganizationCreateSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    gate = _gate_or_error(body.invitation_id)
    errors = name_errors(query_bus, body.name, body.short_name)
    logo = logo_from_body(body, None, errors)

    if errors:
        raise FieldValidationError(errors=errors)

    kwargs = dict(
        actor=actor(),
        name=body.name,
        short_name=body.short_name,
        description=body.description,
        location=location_value_object(body.location),
        logo=logo,
        url=body.url,
        email=body.email,
        phone=body.phone,
        fax=body.fax,
    )

    options = get_embedded_relation_options(gate.invitation)

    if gate.invitation:
        kwargs["invitation_id"] = gate.invitation.id
    elif options:
        kwargs["current_admin_unit_id"] = options.admin_unit.id
        kwargs["embedded_relation_verify"] = body.relation_verify and options.can_verify
        kwargs["embedded_relation_auto_verify_event_reference_requests"] = (
            body.relation_auto_verify_event_reference_requests
            and options.can_auto_verify
        )

    result = message_bus.handle_command(CreateOrganizationCommand(**kwargs))

    if not result.verified:
        flash(
            gettext(
                "The organization is not verified. Events are therefore not publicly visible."
            ),
            "warning",
        )

    flash(gettext("Organization successfully created"), "success")

    redirect_url = (
        url_for("main.manage_admin_unit", id=result.id)
        if result.verified
        else url_for(
            "manage_admin_unit.outgoing_organization_verification_requests",
            id=result.id,
        )
    )

    return OrganizationCreated(
        id=result.id, verified=result.verified, redirect_url=redirect_url
    )
