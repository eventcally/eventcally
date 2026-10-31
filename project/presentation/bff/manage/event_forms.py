from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from dateutil.relativedelta import relativedelta
from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext, to_user_timezone
from markupsafe import Markup, escape

from project.application.commands import (
    CreateEventCommand,
    RequestEventReferenceCommand,
    UpdateEventCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetCustomEventCategoryQuery,
    GetEventCategoryByNameQuery,
    GetEventCategoryQuery,
    GetEventForEditQuery,
    GetEventOrganizerRefQuery,
    GetEventPlaceRefQuery,
    ListAllEventCategoriesQuery,
    ListCustomEventCategorySetsQuery,
    ListReferenceRequestSuggestionsQuery,
    LookupCustomEventCategoriesQuery,
    PageRequest,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.translation import dummy_gettext
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.events import LOOKUP_PER_PAGE
from project.presentation.bff.manage.image_form import image_form_value, image_from_save
from project.presentation.bff.manage.organization_form import actor, license_choices
from project.presentation.bff.manage.schemas import (
    CustomEventCategoryLookupParams,
    CustomEventCategorySetChoice,
    EventCreate,
    EventDateDefinition,
    EventForm,
    EventFormChoice,
    EventFormParams,
    EventOccurrence,
    EventOccurrenceList,
    EventOccurrencesParams,
    EventSaveBase,
    EventSaved,
    EventUpdate,
    ManageRef,
    ManageRefList,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import (
    can_request_event_reference_from_admin_unit,
    get_admin_unit_for_manage,
    has_access,
)
from project.presentation.shared.event_rating import event_rating_choices
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.reference_request import (
    get_success_text_for_request_creation,
)
from project.shared.dateutils import (
    berlin_tz,
    calculate_occurrences,
    date_set_end_of_day,
    get_next_full_hour,
)
from project.shared.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_place_str,
)

OCCURRENCES_BATCH_SIZE = 10
MAX_DURATION_DAYS = 180

_STATUSES = list(EventStatus)
# The order of the legacy select.
_PUBLIC_STATUSES = [
    EventPublicStatus.published,
    EventPublicStatus.planned,
    EventPublicStatus.draft,
]


def _write_access_or_forbidden(id: int):
    if not has_access(SimpleNamespace(id=id), "events:write"):
        raise UnauthorizedError()


def _event_or_404(id: int, event_id: int, query_bus: QueryBus):
    _write_access_or_forbidden(id)
    event = result_or_404(query_bus.handle(GetEventForEditQuery(id=event_id)))

    # Do not reveal the events of other organizations.
    if event.admin_unit_id != id:
        abort(404)

    return event


def _to_wall_clock(value: Optional[datetime]) -> Optional[datetime]:
    """The naive Berlin wall-clock time the date and time inputs show."""
    if value is None:
        return None

    return to_user_timezone(value).replace(tzinfo=None)


def _from_wall_clock(value: Optional[datetime]) -> Optional[datetime]:
    """A naive wall-clock time of the form as Berlin time."""
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.astimezone(berlin_tz)

    return value.replace(tzinfo=berlin_tz)


# `get_localized_enum_name` builds these msgids at runtime, so extraction cannot find
# them. Keep the ones no template or component names literally.
_ENUM_LABELS = (
    dummy_gettext("EventAttendanceMode.offline"),
    dummy_gettext("EventPublicStatus.published"),
    dummy_gettext("EventStatus.scheduled"),
    dummy_gettext("EventTargetGroupOrigin.both"),
    dummy_gettext("EventTargetGroupOrigin.resident"),
    dummy_gettext("EventTargetGroupOrigin.tourist"),
)


def _choices(members) -> list[EventFormChoice]:
    return [
        EventFormChoice(value=int(member), label=str(get_localized_enum_name(member)))
        for member in members
    ]


def _rating_choices() -> list[EventFormChoice]:
    return [
        EventFormChoice(value=value, label=str(label))
        for value, label in event_rating_choices
    ]


def _category_choices(query_bus: QueryBus) -> list[ManageRef]:
    categories = query_bus.handle(ListAllEventCategoriesQuery())
    choices = [
        ManageRef(id=category.id, name=str(get_event_category_name(category)))
        for category in categories
    ]
    return sorted(choices, key=lambda choice: choice.name)


def _custom_category_sets(query_bus: QueryBus, event=None):
    categories = event.custom_categories if event else []
    return [
        CustomEventCategorySetChoice(
            id=category_set.id,
            label=category_set.label_or_name,
            selected=[
                ManageRef(id=category.id, name=category.label_or_name)
                for category in categories
                if category.category_set_id == category_set.id
            ],
        )
        for category_set in query_bus.handle(ListCustomEventCategorySetsQuery()).items
    ]


def _date_definitions(event) -> list[EventDateDefinition]:
    return [
        EventDateDefinition(
            start=_to_wall_clock(definition.start),
            end=_to_wall_clock(definition.end),
            allday=definition.allday,
            recurrence_rule=definition.recurrence_rule,
        )
        for definition in event.date_definitions
    ]


def _base_form(id: int, query_bus: QueryBus) -> dict:
    return dict(
        category_choices=_category_choices(query_bus),
        licenses=license_choices(query_bus),
        target_group_origin=int(EventTargetGroupOrigin.both),
        target_group_origin_choices=_choices(list(EventTargetGroupOrigin)),
        attendance_mode=int(EventAttendanceMode.offline),
        attendance_mode_choices=_choices(list(EventAttendanceMode)),
        rating_choices=_rating_choices(),
        can_create_place=has_access(SimpleNamespace(id=id), "event_places:write"),
        can_create_organizer=has_access(
            SimpleNamespace(id=id), "event_organizers:write"
        ),
    )


def _event_fields(event, own: bool) -> dict:
    """The fields of the form filled from `event`. Without `own` (a template of
    another organization) the fields that belong to that organization stay empty."""
    result = dict(
        name=event.name,
        description=event.description,
        date_definitions=_date_definitions(event),
        category_ids=[category.id for category in event.categories],
        photo=image_form_value(event.photo),
        external_link=event.external_link,
        ticket_link=event.ticket_link,
        tags=event.tags,
        kid_friendly=bool(event.kid_friendly),
        accessible_for_free=bool(event.accessible_for_free),
        registration_required=bool(event.registration_required),
        booked_up=bool(event.booked_up),
        age_from=event.age_from,
        age_to=event.age_to,
        expected_participants=event.expected_participants,
        price_info=event.price_info,
    )

    if event.target_group_origin is not None:
        result["target_group_origin"] = int(event.target_group_origin)

    if event.attendance_mode is not None:
        result["attendance_mode"] = int(event.attendance_mode)

    if own:
        result.update(
            organizer=(
                ManageRef(id=event.organizer.id, name=event.organizer.name)
                if event.organizer
                else None
            ),
            event_place=(
                ManageRef(
                    id=event.event_place.id, name=get_place_str(event.event_place)
                )
                if event.event_place
                else None
            ),
            co_organizers=[
                ManageRef(id=organizer.id, name=organizer.name)
                for organizer in event.co_organizers
            ],
            internal_tags=event.internal_tags,
        )

        if event.rating is not None:
            result["rating"] = event.rating

    return result


def _reference_request_suggestions(id: int, query_bus: QueryBus):
    admin_unit = get_admin_unit_for_manage(id)

    if not can_request_event_reference_from_admin_unit(admin_unit):
        return [], []

    suggestions = query_bus.handle(
        ListReferenceRequestSuggestionsQuery(admin_unit_id=id)
    )
    choices = sorted(
        [ManageRef(id=a.id, name=a.name) for a in suggestions.choices],
        key=lambda a: a.name,
    )
    return choices, list(suggestions.selected_ids)


def _required(loc: list, errors: list):
    errors.append((loc, gettext("This field is required.")))


def _date_errors(definitions: list[EventDateDefinition], errors: list):
    """Copied from `EventDateDefinitionFormMixin.validate_date_definition` (legacy
    form): the start before the end, at most 180 days (wall clock)."""
    for index, definition in enumerate(definitions):
        start = _from_wall_clock(definition.start)
        end = _from_wall_clock(definition.end)

        if not end:
            continue

        if start > end:
            errors.append(
                (
                    ["date_definitions", str(index), "start"],
                    gettext("The start must be before the end."),
                )
            )
            continue

        if definition.allday:
            end = date_set_end_of_day(end)

        if end > start + relativedelta(days=MAX_DURATION_DAYS):
            errors.append(
                (
                    ["date_definitions", str(index), "end"],
                    gettext("An event can last a maximum of 180 days."),
                )
            )


def _invalid_choice(loc: list, errors: list):
    errors.append((loc, gettext("Not a valid choice")))


def _validate(id: int, body: EventSaveBase, query_bus: QueryBus) -> list:
    errors = []
    _date_errors(body.date_definitions, errors)

    if body.organizer_id is None:
        _required(["organizer_id"], errors)
    elif not query_bus.handle(
        GetEventOrganizerRefQuery(admin_unit_id=id, id=body.organizer_id)
    ):
        _invalid_choice(["organizer_id"], errors)

    if body.event_place_id is None:
        _required(["event_place_id"], errors)
    elif not query_bus.handle(
        GetEventPlaceRefQuery(admin_unit_id=id, id=body.event_place_id)
    ):
        _invalid_choice(["event_place_id"], errors)

    for organizer_id in body.co_organizer_ids:
        if not query_bus.handle(
            GetEventOrganizerRefQuery(admin_unit_id=id, id=organizer_id)
        ):
            _invalid_choice(["co_organizer_ids"], errors)
            break

    if not body.category_ids:
        _required(["category_ids"], errors)

    for category_id in body.category_ids:
        if not query_bus.handle(GetEventCategoryQuery(id=category_id)):
            _invalid_choice(["category_ids"], errors)
            break

    for category_id in body.custom_category_ids:
        if not query_bus.handle(GetCustomEventCategoryQuery(id=category_id)):
            _invalid_choice(["custom_category_ids"], errors)
            break

    return errors


def _date_definition_value_objects(body: EventSaveBase):
    return [
        EventDateDefinitionValueObject(
            start=_from_wall_clock(definition.start),
            end=_from_wall_clock(definition.end),
            allday=definition.allday,
            recurrence_rule=definition.recurrence_rule,
        )
        for definition in body.date_definitions
    ]


def _command_fields(body: EventSaveBase, photo) -> dict:
    return dict(
        name=body.name,
        organizer_id=body.organizer_id,
        event_place_id=body.event_place_id,
        date_definitions=_date_definition_value_objects(body),
        description=body.description,
        external_link=body.external_link,
        ticket_link=body.ticket_link,
        tags=body.tags,
        internal_tags=body.internal_tags,
        kid_friendly=body.kid_friendly,
        accessible_for_free=body.accessible_for_free,
        age_from=body.age_from,
        age_to=body.age_to,
        registration_required=body.registration_required,
        booked_up=body.booked_up,
        expected_participants=body.expected_participants,
        price_info=body.price_info,
        target_group_origin=body.target_group_origin,
        attendance_mode=body.attendance_mode,
        photo=photo,
        category_ids=set(body.category_ids),
        custom_category_ids=set(body.custom_category_ids),
        rating=body.rating,
        co_organizer_ids=set(body.co_organizer_ids),
    )


def _flash_with_link(msg: str, url: str):
    """Copied from `flash_message` (web views): the message plus a " – Show" link."""
    link = Markup(' &ndash; <a href="%s">%s</a>') % (url, gettext("Show"))
    flash(escape(msg) + link, "success")


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/create-form",
    query=EventFormParams,
    response=EventForm,
    summary="Get the form to create an event",
)
@inject
def get_event_create_form(
    id: int,
    query: EventFormParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    form = _base_form(id, query_bus)
    choices, selected_ids = _reference_request_suggestions(id, query_bus)
    form.update(reference_request_choices=choices, reference_request_ids=selected_ids)

    if query.template_id:
        # A template of another organization is allowed (read visibility applies).
        template = result_or_404(
            query_bus.handle(GetEventForEditQuery(id=query.template_id))
        )
        form.update(_event_fields(template, own=template.admin_unit_id == id))
        form["custom_category_sets"] = _custom_category_sets(query_bus, template)
        return EventForm(**form)

    category = query_bus.handle(GetEventCategoryByNameQuery(name="Other"))
    form.update(
        date_definitions=[
            EventDateDefinition(start=_to_wall_clock(get_next_full_hour()))
        ],
        category_ids=[category.id] if category else [],
        custom_category_sets=_custom_category_sets(query_bus),
    )
    return EventForm(**form)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>/form",
    response=EventForm,
    summary="Get the form to update an event",
)
@inject
def get_event_form(
    id: int,
    event_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    event = _event_or_404(id, event_id, query_bus)
    form = _base_form(id, query_bus)
    form.update(_event_fields(event, own=True))
    form.update(
        id=event.id,
        status=int(event.status or EventStatus.scheduled),
        public_status=int(event.public_status),
        status_choices=_choices(_STATUSES),
        public_status_choices=_choices(_PUBLIC_STATUSES),
        custom_category_sets=_custom_category_sets(query_bus, event),
    )
    return EventForm(**form)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events",
    method="POST",
    body=EventCreate,
    response=EventSaved,
    status=201,
    summary="Create an event",
)
@inject
def create_event(
    id: int,
    body: EventCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    errors = _validate(id, body, query_bus)
    photo = image_from_save(body.photo, None, errors, ["photo"])

    reference_names = {}
    if body.reference_request_ids:
        choices, _ = _reference_request_suggestions(id, query_bus)
        reference_names = {choice.id: choice.name for choice in choices}

        if any(i not in reference_names for i in body.reference_request_ids):
            _invalid_choice(["reference_request_ids"], errors)

    if errors:
        raise FieldValidationError(errors=errors)

    result = message_bus.handle_command(
        CreateEventCommand(
            actor=actor(),
            admin_unit_id=id,
            status=EventStatus.scheduled,
            public_status=body.public_status,
            **_command_fields(body, photo),
        )
    )

    success_msg = (
        gettext("Event successfully published")
        if body.public_status == EventPublicStatus.published
        else (
            gettext("Draft successfully saved")
            if body.public_status == EventPublicStatus.draft
            else gettext("Event successfully planned")
        )
    )
    _flash_with_link(success_msg, url_for("main.event", event_id=result.id))

    if body.public_status == EventPublicStatus.published:
        for target_admin_unit_id in body.reference_request_ids:
            reference_result = message_bus.handle_command(
                RequestEventReferenceCommand(
                    actor=actor(),
                    admin_unit_id=target_admin_unit_id,
                    event_id=result.id,
                )
            )
            flash(
                get_success_text_for_request_creation(
                    reference_names.get(target_admin_unit_id),
                    reference_result.verified,
                ),
                "success",
            )

    return EventSaved(
        id=result.id, redirect_url=url_for("main.event_actions", event_id=result.id)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/<int:event_id>",
    method="PUT",
    body=EventUpdate,
    response=EventSaved,
    summary="Update an event",
)
@inject
def update_event(
    id: int,
    event_id: int,
    body: EventUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    event = _event_or_404(id, event_id, query_bus)
    errors = _validate(id, body, query_bus)
    photo = image_from_save(body.photo, event.photo, errors, ["photo"])

    if errors:
        raise FieldValidationError(errors=errors)

    message_bus.handle_command(
        UpdateEventCommand(
            actor=actor(),
            id=event_id,
            status=body.status,
            public_status=body.public_status,
            **_command_fields(body, photo),
        )
    )

    flash(
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=gettext("Event"),
        ),
        "success",
    )
    return EventSaved(
        id=event_id, redirect_url=url_for("manage_admin_unit.events", id=id)
    )


def _occurrences(start: datetime, rrule: str, batch_start: int) -> dict:
    return calculate_occurrences(
        start, "%d.%m.%Y", rrule, batch_start, OCCURRENCES_BATCH_SIZE
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/events/occurrences",
    method="POST",
    body=EventOccurrencesParams,
    response=EventOccurrenceList,
    summary="Preview the occurrences of a recurrence rule",
)
def get_event_occurrences(id: int, body: EventOccurrencesParams):
    """Copied from `main.event_rrule` (web views): the dates of the rule from the
    start day on, ten per batch."""
    _write_access_or_forbidden(id)
    start = datetime(body.start.year, body.start.month, body.start.day)

    try:
        result = _occurrences(start, body.rrule, body.batch_start)
        following = _occurrences(
            start, body.rrule, body.batch_start + OCCURRENCES_BATCH_SIZE
        )
    except Exception:
        raise FieldValidationError(["rrule"], gettext("Not a valid choice"))

    return EventOccurrenceList(
        items=[
            EventOccurrence(
                date=o["date"], formatted_date=o["formattedDate"], type=o["type"]
            )
            for o in result["occurrences"]
        ],
        has_more=any(o["type"] != "exdate" for o in following["occurrences"]),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/custom-event-categories",
    query=CustomEventCategoryLookupParams,
    response=ManageRefList,
    summary="Look up the categories of a custom event category set",
)
@inject
def lookup_custom_event_categories(
    id: int,
    query: CustomEventCategoryLookupParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    page = query_bus.handle(
        LookupCustomEventCategoriesQuery(
            category_set_id=query.set_id,
            term=query.keyword,
            page=PageRequest(page=1, per_page=LOOKUP_PER_PAGE),
        )
    )
    return ManageRefList(
        items=[ManageRef(id=c.id, name=c.label_or_name) for c in page.items]
    )
