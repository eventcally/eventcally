from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import current_app
from flask_babel import gettext

from project.application.commands import UpdateOrganizationCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetOrganizationSettingsQuery,
    IsOrganizationNameTakenQuery,
    IsOrganizationShortNameTakenQuery,
    ListLicensesQuery,
)
from project.application.queries.page_request import MAX_PER_PAGE, PageRequest
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.schemas import (
    OrganizationNameAvailability,
    OrganizationNameAvailabilityParams,
    OrganizationSettingsForm,
    OrganizationSettingsLocationView,
    OrganizationSettingsLogo,
    OrganizationSettingsSave,
    OrganizationSettingsVerificationRequests,
    PlanningChoice,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.images import image_value_object_from_data_uri
from project.presentation.shared.query_results import result_or_404
from project.shared.imageutils import get_data_uri_from_bytes


def _actor():
    return current_app.container.context.context_provider().current_actor


def _settings_or_forbidden(id: int, query_bus: QueryBus):
    if not has_access(SimpleNamespace(id=id), "settings:write"):
        raise UnauthorizedError()

    return result_or_404(query_bus.handle(GetOrganizationSettingsQuery(id=id)))


def _float_or_none(value):
    return None if value is None else float(value)


def _license_name(license) -> str:
    return f"{license.code} ({license.name})"


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
    licenses = query_bus.handle(
        ListLicensesQuery(page=PageRequest(per_page=MAX_PER_PAGE))
    )
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
            OrganizationSettingsLogo(
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
        licenses=[
            PlanningChoice(id=license.id, name=_license_name(license))
            for license in licenses.items
        ],
        deletion_requested_at=settings.deletion_requested_at,
    )


def _logo_from_body(body: OrganizationSettingsSave, settings, errors: list):
    logo = body.logo

    if logo is None:
        return None

    image = None

    if logo.image_base64 is None:
        stored = settings.logo
        if stored and stored.data:
            image = ImageValueObject(
                data=stored.data,
                encoding_format=stored.encoding_format,
                copyright_text=logo.copyright_text,
                license_id=logo.license_id,
            )
    else:
        try:
            image = image_value_object_from_data_uri(
                logo.image_base64, logo.copyright_text, logo.license_id
            )
        except Exception as e:
            errors.append((["logo", "image_base64"], str(e)))

    if image is not None and not (logo.copyright_text or "").strip():
        errors.append((["logo", "copyright_text"], gettext("This field is required.")))

    return image


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
    errors = []

    if query_bus.handle(IsOrganizationNameTakenQuery(name=body.name, exclude_id=id)):
        errors.append((["name"], gettext("Name is already taken")))

    if query_bus.handle(
        IsOrganizationShortNameTakenQuery(short_name=body.short_name, exclude_id=id)
    ):
        errors.append((["short_name"], gettext("Short name is already taken")))

    logo = _logo_from_body(body, settings, errors)

    if errors:
        raise FieldValidationError(errors=errors)

    kwargs = dict(
        actor=_actor(),
        id=id,
        name=body.name,
        short_name=body.short_name,
        description=body.description,
        location=LocationValueObject(
            street=body.location.street,
            postalCode=body.location.postalCode,
            city=body.location.city,
            state=body.location.state,
            latitude=body.location.latitude,
            longitude=body.location.longitude,
        ),
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


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/settings/name-availability",
    query=OrganizationNameAvailabilityParams,
    response=OrganizationNameAvailability,
    summary="Whether the name and short name of an organization are taken",
)
@inject
def get_organization_name_availability(
    id: int,
    query: OrganizationNameAvailabilityParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _settings_or_forbidden(id, query_bus)
    result = OrganizationNameAvailability()

    if query.name:
        result.name_taken = query_bus.handle(
            IsOrganizationNameTakenQuery(name=query.name, exclude_id=id)
        )

    if query.short_name:
        result.short_name_taken = query_bus.handle(
            IsOrganizationShortNameTakenQuery(
                short_name=query.short_name, exclude_id=id
            )
        )

    return result
