"""Eager loads and mappers from `Event` to the event read models.

`event_load_options` loads everything `to_event_search_item` / `to_event_detail` read,
so mapping inside the read session never lazy-loads.
"""

from typing import Dict, Iterable, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Load, joinedload, selectinload

from project.application.read_models.event_read_models import (
    EventCustomCategoryReadModel,
    EventDateDefinitionDetailReadModel,
    EventDetailReadModel,
    EventEditReadModel,
    EventOrganizationReadModel,
    EventOrganizerEmbedReadModel,
    EventPlaceEmbedReadModel,
    EventReferenceItemReadModel,
    EventReferenceRequestItemReadModel,
    EventSearchItemReadModel,
    OrganizationBadgeReadModel,
)
from project.application.read_models.reference_data_read_models import (
    CustomEventCategorySetRefReadModel,
    EventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    AppInstallation,
    CustomEventCategory,
    Event,
    EventDate,
    EventOrganizer,
    EventPlace,
    EventReference,
    EventReferenceRequest,
    Image,
    OAuth2Client,
    User,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    _actor_label,
    to_image_edit_read_model,
    to_image_read_model,
    to_location_read_model,
)


def _path(first, *relationships):
    """A loader following `first` (e.g. `joinedload(Event.admin_unit)`) down the
    given relationships. Loader options are generative: every option is chained
    from the root and nothing is mutated in place."""
    loader = first

    for relationship in relationships:
        loader = loader.joinedload(relationship)

    return loader


def _image_options(first, *relationships) -> list:
    """The image at the end of the path, with its timestamps (for the cache hash)
    and its license."""
    return [
        _path(first, *relationships)
        .undefer(Image.created_at)
        .undefer(Image.updated_at),
        _path(first, *relationships, Image.license),
    ]


def _organizer_options(first) -> list:
    return [
        _path(first).undefer_group("detail").undefer_group("trackable"),
        _path(first, EventOrganizer.location),
        *_image_options(first, EventOrganizer.logo),
    ]


def _installation_label_options(relationship) -> list:
    return [
        joinedload(relationship).load_only(
            AppInstallation.id, AppInstallation.oauth2_client_id
        ),
        joinedload(relationship)
        .joinedload(AppInstallation.oauth2_client)
        .load_only(OAuth2Client.id, OAuth2Client._client_metadata),
    ]


def audit_label_options() -> list:
    """Loads for `created_by_label` / `updated_by_label` of the event."""
    return [
        joinedload(Event.created_by).load_only(User.id, User.email),
        joinedload(Event.updated_by).load_only(User.id, User.email),
        *_installation_label_options(Event.created_by_app_installation),
        *_installation_label_options(Event.updated_by_app_installation),
    ]


def event_load_options(co_organizers: bool = False, audit: bool = False) -> list:
    options = [
        # Bound to `Event`: an unbound wildcard also reaches the collection loads.
        Load(Event).undefer_group("trackable"),
        joinedload(Event.admin_unit)
        .undefer(AdminUnit.logo_id)
        .undefer_group("detail")
        .undefer_group("trackable"),
        joinedload(Event.admin_unit).joinedload(AdminUnit.location),
        *_image_options(joinedload(Event.admin_unit), AdminUnit.logo),
        joinedload(Event.event_place).undefer_group("trackable"),
        joinedload(Event.event_place).joinedload(EventPlace.location),
        *_image_options(joinedload(Event.event_place), EventPlace.photo),
        *_organizer_options(joinedload(Event.organizer)),
        *_image_options(joinedload(Event.photo)),
        selectinload(Event.categories),
        selectinload(Event.custom_categories).joinedload(
            CustomEventCategory.category_set
        ),
        selectinload(Event.date_definitions),
    ]

    if co_organizers:
        options.extend(_organizer_options(selectinload(Event.co_organizers)))

    if audit:
        options.extend(audit_label_options())

    return options


def verified_admin_units(session, admin_unit_ids: Iterable[ObjectId]) -> Dict:
    """`AdminUnit.is_verified` is a correlated subquery, not a column: one batch."""
    ids = set(admin_unit_ids)

    if not ids:
        return {}

    rows = session.execute(
        select(AdminUnit.id, AdminUnit.is_verified).where(AdminUnit.id.in_(ids))
    ).all()
    return {row[0]: bool(row[1]) for row in rows}


def reference_ids(
    session, event_ids: Iterable[ObjectId], admin_unit_id: Optional[ObjectId]
) -> Dict:
    """event id → reference id of the references the organization holds."""
    ids = set(event_ids)

    if not ids or admin_unit_id is None:
        return {}

    rows = session.execute(
        select(EventReference.event_id, EventReference.id).where(
            EventReference.admin_unit_id == admin_unit_id,
            EventReference.event_id.in_(ids),
        )
    ).all()
    return {row[0]: row[1] for row in rows}


def _to_organizer(organizer) -> Optional[EventOrganizerEmbedReadModel]:
    if organizer is None:
        return None

    return EventOrganizerEmbedReadModel(
        id=organizer.id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        created_at=organizer.created_at,
        updated_at=organizer.updated_at,
        location=to_location_read_model(organizer.location),
        logo=to_image_read_model(organizer.logo),
    )


def _to_place(place) -> Optional[EventPlaceEmbedReadModel]:
    if place is None:
        return None

    return EventPlaceEmbedReadModel(
        id=place.id,
        name=place.name,
        url=place.url,
        description=place.description,
        admin_unit_id=place.admin_unit_id,
        created_at=place.created_at,
        updated_at=place.updated_at,
        location=to_location_read_model(place.location),
        photo=to_image_read_model(place.photo),
    )


def _to_organization(admin_unit, is_verified: bool) -> EventOrganizationReadModel:
    return EventOrganizationReadModel(
        id=admin_unit.id,
        name=admin_unit.name,
        short_name=admin_unit.short_name,
        url=admin_unit.url,
        email=admin_unit.email,
        phone=admin_unit.phone,
        fax=admin_unit.fax,
        description=admin_unit.description,
        is_verified=is_verified,
        created_at=admin_unit.created_at,
        updated_at=admin_unit.updated_at,
        location=to_location_read_model(admin_unit.location),
        logo=to_image_read_model(admin_unit.logo),
    )


def _event_fields(event, is_verified: bool, reference_id: Optional[ObjectId]) -> dict:
    return dict(
        id=event.id,
        name=event.name,
        description=event.description,
        external_link=event.external_link,
        ticket_link=event.ticket_link,
        tags=event.tags,
        internal_tags=event.internal_tags,
        kid_friendly=event.kid_friendly,
        accessible_for_free=event.accessible_for_free,
        age_from=event.age_from,
        age_to=event.age_to,
        target_group_origin=event.target_group_origin,
        attendance_mode=event.attendance_mode,
        status=event.status,
        public_status=event.public_status,
        registration_required=event.registration_required,
        booked_up=event.booked_up,
        expected_participants=event.expected_participants,
        price_info=event.price_info,
        rating=event.rating,
        created_at=event.created_at,
        updated_at=event.updated_at,
        admin_unit_id=event.admin_unit_id,
        organizer_id=event.organizer_id,
        event_place_id=event.event_place_id,
        is_recurring=any(d.recurrence_rule for d in event.date_definitions),
        reference_id=reference_id,
        date_definitions=[
            EventDateDefinitionDetailReadModel(
                id=d.id,
                start=d.start,
                end=d.end,
                allday=d.allday,
                recurrence_rule=d.recurrence_rule,
            )
            for d in event.date_definitions
        ],
        photo=to_image_read_model(event.photo),
        event_place=_to_place(event.event_place),
        organizer=_to_organizer(event.organizer),
        admin_unit=_to_organization(event.admin_unit, is_verified),
        categories=[
            EventCategoryRefReadModel(id=c.id, name=c.name) for c in event.categories
        ],
        custom_categories=[
            EventCustomCategoryReadModel(
                id=c.id,
                name=c.name,
                label=c.label,
                category_set=CustomEventCategorySetRefReadModel(
                    id=c.category_set.id,
                    name=c.category_set.name,
                    label=c.category_set.label,
                ),
            )
            for c in event.custom_categories
        ],
    )


def event_counts(session, event_ids: Iterable[ObjectId]) -> Dict:
    """event id → (dates, references, reference requests), for the manage list."""
    ids = set(event_ids)

    if not ids:
        return {}

    def counted(model):
        rows = session.execute(
            select(model.event_id, func.count())
            .where(model.event_id.in_(ids))
            .group_by(model.event_id)
        ).all()
        return {row[0]: row[1] for row in rows}

    dates = counted(EventDate)
    references = counted(EventReference)
    requests = counted(EventReferenceRequest)
    return {
        event_id: dict(
            number_of_dates=dates.get(event_id, 0),
            number_of_references=references.get(event_id, 0),
            number_of_reference_requests=requests.get(event_id, 0),
        )
        for event_id in ids
    }


def to_event_search_item(
    event,
    is_verified: bool,
    reference_id: Optional[ObjectId] = None,
    counts: Optional[dict] = None,
) -> EventSearchItemReadModel:
    return EventSearchItemReadModel(
        **_event_fields(event, is_verified, reference_id), **(counts or {})
    )


def to_event_detail(
    event,
    is_verified: bool,
    reference_id: Optional[ObjectId] = None,
    references: Optional[list] = None,
    reference_requests: Optional[list] = None,
) -> EventDetailReadModel:
    """Needs `event_load_options(co_organizers=True, audit=True)`."""
    return EventDetailReadModel(
        **_event_fields(event, is_verified, reference_id),
        co_organizers=[_to_organizer(o) for o in event.co_organizers],
        references=references or [],
        reference_requests=reference_requests or [],
        created_by_label=_actor_label(
            event.created_by, event.created_by_app_installation
        ),
        updated_by_label=_actor_label(
            event.updated_by, event.updated_by_app_installation
        ),
    )


def event_references(session, event_ids: Iterable[ObjectId]) -> Dict:
    """event id → the organizations referencing it (with their verified badge)."""
    ids = set(event_ids)

    if not ids:
        return {}

    rows = session.execute(
        select(
            EventReference.id,
            EventReference.event_id,
            AdminUnit.id,
            AdminUnit.name,
            AdminUnit.is_verified,
        )
        .join(AdminUnit, AdminUnit.id == EventReference.admin_unit_id)
        .where(EventReference.event_id.in_(ids))
        .order_by(EventReference.id)
    ).all()
    result: Dict = {}

    for row in rows:
        result.setdefault(row[1], []).append(
            EventReferenceItemReadModel(
                id=row[0],
                admin_unit=OrganizationBadgeReadModel(
                    id=row[2], name=row[3], is_verified=bool(row[4])
                ),
            )
        )

    return result


def event_reference_requests(session, event_ids: Iterable[ObjectId]) -> Dict:
    """event id → the reference requests sent for it."""
    ids = set(event_ids)

    if not ids:
        return {}

    rows = session.execute(
        select(
            EventReferenceRequest.id,
            EventReferenceRequest.event_id,
            EventReferenceRequest.review_status,
            EventReferenceRequest.rejection_reason,
            AdminUnit.id,
            AdminUnit.name,
            AdminUnit.is_verified,
        )
        .join(AdminUnit, AdminUnit.id == EventReferenceRequest.admin_unit_id)
        .where(EventReferenceRequest.event_id.in_(ids))
        .order_by(EventReferenceRequest.id)
    ).all()
    result: Dict = {}

    for row in rows:
        result.setdefault(row[1], []).append(
            EventReferenceRequestItemReadModel(
                id=row[0],
                review_status=row[2],
                rejection_reason=row[3],
                admin_unit=OrganizationBadgeReadModel(
                    id=row[4], name=row[5], is_verified=bool(row[6])
                ),
            )
        )

    return result


def event_edit_load_options() -> list:
    """`event_load_options` plus the photo data the update form shows again."""
    return [
        *event_load_options(co_organizers=True),
        _path(joinedload(Event.photo)).undefer(Image.data),
    ]


def to_event_edit(event, is_verified: bool) -> EventEditReadModel:
    """Needs `event_edit_load_options`."""
    fields = _event_fields(event, is_verified, None)
    fields["photo"] = to_image_edit_read_model(event.photo)

    return EventEditReadModel(
        **fields, co_organizers=[_to_organizer(o) for o in event.co_organizers]
    )


# Public names for the other read repositories.
to_organizer_embed = _to_organizer
to_place_embed = _to_place
to_organization_embed = _to_organization
image_options = _image_options
