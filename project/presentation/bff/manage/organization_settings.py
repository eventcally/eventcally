from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject

from project.application.commands import UpdateOrganizationCommand
from project.application.message_bus import MessageBus
from project.application.queries import GetOrganizationSettingsQuery
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
    OrganizationLogo,
    OrganizationSettingsForm,
    OrganizationSettingsLocationView,
    OrganizationSettingsSave,
    OrganizationSettingsVerificationRequests,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404
from project.shared.imageutils import get_data_uri_from_bytes


def _settings_or_forbidden(id: int, query_bus: QueryBus):
    if not has_access(SimpleNamespace(id=id), "settings:write"):
        raise UnauthorizedError()

    return result_or_404(query_bus.handle(GetOrganizationSettingsQuery(id=id)))


def _float_or_none(value):
    return None if value is None else float(value)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/settings",
    response=OrganizationSettingsForm,
    summary="Get the settings form of an organization",
)
@inject
def get_organization_settings(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    settings = _settings_or_forbidden(id, query_bus)
    location = settings.location
    logo = settings.logo

    return OrganizationSettingsForm(
        id=settings.id,
        name=settings.name,
        short_name=settings.short_name or "",
        description=settings.description,
        location=(
            OrganizationSettingsLocationView(
                street=location.street or "",
                postalCode=location.postalCode or "",
                city=location.city or "",
                state=location.state or "",
                latitude=_float_or_none(location.latitude),
                longitude=_float_or_none(location.longitude),
            )
            if location
            else OrganizationSettingsLocationView()
        ),
        logo=(
            OrganizationLogo(
                image_base64=get_data_uri_from_bytes(logo.data, logo.encoding_format),
                copyright_text=logo.copyright_text,
                license_id=logo.license.id if logo.license else None,
            )
            if logo and logo.data
            else None
        ),
        url=settings.url,
        email=settings.email,
        phone=settings.phone,
        fax=settings.fax,
        can_verify_other=settings.can_verify_other,
        verification_requests=(
            OrganizationSettingsVerificationRequests(
                allowed=settings.incoming_verification_requests_allowed,
                text=settings.incoming_verification_requests_text,
                postal_codes=settings.incoming_verification_requests_postal_codes,
            )
            if settings.can_verify_other
            else None
        ),
        licenses=license_choices(query_bus),
        deletion_requested_at=settings.deletion_requested_at,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/settings",
    method="PUT",
    body=OrganizationSettingsSave,
    summary="Update the settings of an organization",
)
@inject
def update_organization_settings(
    id: int,
    body: OrganizationSettingsSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    settings = _settings_or_forbidden(id, query_bus)
    errors = name_errors(query_bus, body.name, body.short_name, exclude_id=id)
    logo = logo_from_body(body, settings.logo, errors)

    if errors:
        raise FieldValidationError(errors=errors)

    kwargs = dict(
        actor=actor(),
        id=id,
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

    if settings.can_verify_other and body.verification_requests:
        verification = body.verification_requests
        kwargs["incoming_verification_requests_allowed"] = verification.allowed
        kwargs["incoming_verification_requests_text"] = verification.text
        kwargs["incoming_verification_requests_postal_codes"] = (
            verification.postal_codes
        )

    message_bus.handle_command(UpdateOrganizationCommand(**kwargs))
