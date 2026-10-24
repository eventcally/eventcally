from typing import Optional

from flask import current_app
from flask_babel import gettext

from project.application.queries import (
    IsOrganizationNameTakenQuery,
    IsOrganizationShortNameTakenQuery,
    ListLicensesQuery,
)
from project.application.queries.page_request import MAX_PER_PAGE, PageRequest
from project.application.query_bus import QueryBus
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.presentation.bff.manage.schemas import (
    OrganizationBaseSave,
    OrganizationLocation,
    PlanningChoice,
)
from project.presentation.shared.images import image_value_object_from_data_uri


def actor():
    return current_app.container.context.context_provider().current_actor


def license_choices(query_bus: QueryBus) -> list[PlanningChoice]:
    licenses = query_bus.handle(
        ListLicensesQuery(page=PageRequest(per_page=MAX_PER_PAGE))
    )
    return [
        PlanningChoice(id=license.id, name=f"{license.code} ({license.name})")
        for license in licenses.items
    ]


def name_errors(
    query_bus: QueryBus, name: str, short_name: str, exclude_id: Optional[int] = None
) -> list:
    errors = []

    if query_bus.handle(IsOrganizationNameTakenQuery(name=name, exclude_id=exclude_id)):
        errors.append((["name"], gettext("Name is already taken")))

    if query_bus.handle(
        IsOrganizationShortNameTakenQuery(short_name=short_name, exclude_id=exclude_id)
    ):
        errors.append((["short_name"], gettext("Short name is already taken")))

    return errors


def location_value_object(location: OrganizationLocation) -> LocationValueObject:
    return LocationValueObject(
        street=location.street,
        postalCode=location.postalCode,
        city=location.city,
        state=location.state,
        latitude=location.latitude,
        longitude=location.longitude,
    )


def logo_from_body(body: OrganizationBaseSave, stored_logo, errors: list):
    """The logo of the save body. `image_base64=None` keeps `stored_logo` (none when
    creating)."""
    logo = body.logo

    if logo is None:
        return None

    image = None

    if logo.image_base64 is None:
        if stored_logo and stored_logo.data:
            image = ImageValueObject(
                data=stored_logo.data,
                encoding_format=stored_logo.encoding_format,
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
