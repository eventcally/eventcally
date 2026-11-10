from datetime import timezone

from flask_babel import gettext

from project.presentation.bff.public.schemas import (
    PublicCalendarLinks,
    PublicCalendarRef,
    PublicEventAudit,
    PublicEventCategoryGroup,
    PublicEventDateRow,
    PublicEventDetail,
    PublicEventOrganization,
    PublicEventOrganizer,
    PublicEventPlace,
    PublicEventReferenceRequest,
    PublicEventReferrer,
    PublicEventRights,
    PublicImage,
    PublicOrganizationBadge,
    PublicOrganizationRef,
    PublicShareLinks,
)
from project.presentation.shared.urls import url_for_image
from project.shared.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_location_str,
    get_place_str,
)

# Enum values the property list does not show (the macro's `ignore`): scheduled,
# both target groups and offline attendance are the unremarkable defaults.
_DEFAULT_ENUM_VALUE = 1


def _image(image, size):
    if not image:
        return None

    return PublicImage(
        url=url_for_image(image, s=size),
        copyright_text=image.copyright_text,
        license_code=image.license.code if image.license else None,
        license_url=image.license.url if image.license else None,
    )


def _address(location):
    if not location:
        return None

    return get_location_str(location) or None


def _utc(value):
    """Audit timestamps are stored as naive UTC; the SPA needs the offset."""
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def _enum_label(value, default_value=_DEFAULT_ENUM_VALUE):
    if not value or value.value == default_value:
        return None

    return str(get_localized_enum_name(value))


def _organizer(organizer):
    return PublicEventOrganizer(
        id=organizer.id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        logo=_image(organizer.logo, 120),
    )


def _badge(organization):
    return PublicOrganizationBadge(
        id=organization.id,
        name=organization.name,
        is_verified=organization.is_verified,
    )


def _category_groups(event):
    groups = []

    if event.categories:
        groups.append(
            PublicEventCategoryGroup(
                label=gettext("Category"),
                names=[str(get_event_category_name(c)) for c in event.categories],
            )
        )

    for custom_categories in event.custom_categories_by_set.values():
        groups.append(
            PublicEventCategoryGroup(
                label=custom_categories[0].category_set.label_or_name,
                names=[c.label_or_name for c in custom_categories],
            )
        )

    return groups


def _reference_request(reference_request):
    status = reference_request.review_status

    return PublicEventReferenceRequest(
        id=reference_request.id,
        review_status=status.name if status else None,
        review_status_label=_enum_label(status, default_value=None),
        organization=_badge(reference_request.admin_unit),
    )


def event_detail(
    event,
    dates,
    *,
    rights: dict,
    show_rating: bool,
    share_links: dict,
    calendar_links: dict,
    public_calendars=None,
    calendar_organization=None,
) -> PublicEventDetail:
    """The public payload of an event. What only editors may see is decided here:
    the rating (`show_rating`), the internal tags and the audit labels follow the
    rights, the reference requests are empty without the right to create them."""
    place = event.event_place
    organization = event.admin_unit
    definition = event.min_start_definition
    can_update = rights["can_update_event"]

    return PublicEventDetail(
        id=event.id,
        name=event.name,
        organization_id=event.admin_unit_id,
        description=event.description,
        external_link=event.external_link,
        ticket_link=event.ticket_link,
        price_info=event.price_info,
        tags=event.tags,
        internal_tags=event.internal_tags if can_update else None,
        kid_friendly=event.kid_friendly,
        accessible_for_free=event.accessible_for_free,
        age_from=event.age_from,
        age_to=event.age_to,
        target_group_origin_label=_enum_label(event.target_group_origin),
        attendance_mode=event.attendance_mode.name if event.attendance_mode else None,
        attendance_mode_label=_enum_label(event.attendance_mode),
        status=event.status.name if event.status else None,
        status_label=_enum_label(event.status),
        public_status=event.public_status.name,
        booked_up=event.booked_up,
        registration_required=event.registration_required,
        expected_participants=event.expected_participants,
        rating=(
            event.rating
            if show_rating and event.rating and event.rating != 50
            else None
        ),
        start=definition.start if definition else None,
        end=definition.end if definition else None,
        allday=definition.allday if definition else False,
        photo=_image(event.photo, 700),
        place=PublicEventPlace(
            id=place.id,
            organization_id=place.admin_unit_id,
            name=place.name,
            description=place.description,
            url=place.url,
            address=_address(place.location),
            city=place.location.city if place.location else None,
            photo=_image(place.photo, 240),
            directions_query=get_place_str(place),
        ),
        organizer=_organizer(event.organizer),
        co_organizers=[_organizer(o) for o in event.co_organizers],
        organization=PublicEventOrganization(
            id=organization.id,
            name=organization.name,
            is_verified=organization.is_verified,
            url=organization.url,
            email=organization.email,
            phone=organization.phone,
            fax=organization.fax,
            address=_address(organization.location),
            logo=_image(organization.logo, 120),
        ),
        categories=_category_groups(event),
        references=[
            PublicEventReferrer(id=r.id, organization=_badge(r.admin_unit))
            for r in event.references
        ],
        reference_requests=(
            [_reference_request(r) for r in event.reference_requests]
            if rights["can_create_reference_request"]
            else []
        ),
        public_calendars=(
            [
                PublicCalendarRef(
                    id=c.id,
                    name=c.name,
                    organization=PublicOrganizationRef(
                        id=c.organization.id, name=c.organization.name
                    ),
                )
                for c in public_calendars
            ]
            if can_update and public_calendars is not None
            else None
        ),
        calendar_organization=(
            PublicOrganizationRef(
                id=calendar_organization.id, name=calendar_organization.name
            )
            if calendar_organization
            else None
        ),
        dates=[
            PublicEventDateRow(id=d.id, start=d.start, end=d.end, allday=d.allday)
            for d in dates
        ],
        rights=PublicEventRights(**rights),
        share_links=PublicShareLinks(**share_links),
        calendar_links=PublicCalendarLinks(**calendar_links),
        audit=PublicEventAudit(
            created_at=_utc(event.created_at),
            updated_at=_utc(event.updated_at),
            created_by_label=event.created_by_label if can_update else None,
            updated_by_label=event.updated_by_label if can_update else None,
        ),
    )
