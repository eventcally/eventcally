"""Map the request of the event searches onto `EventSearchCriteria`.

Mirrors the legacy `EventSearchParams.load_from_request`, which read `request.args`
directly (lists comma-separated or repeated, "0" dropped) and only took the audit
bounds and `sort` from the validated kwargs.
"""

from typing import Optional

from flask import request
from flask_security import current_user

from project.application.queries import EventSearchCriteria, EventSearchSort
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.presentation.shared.query_args import (
    list_arg_from_request,
    trackable_criteria_from_kwargs,
)
from project.shared.dateutils import form_input_to_date
from project.shared.utils import str_to_bool


def _members(enum_type, names: list) -> list:
    return [enum_type[name] for name in names if name in enum_type.__members__]


def reference_admin_unit_id_for_api() -> Optional[int]:
    """The calling organization, whose references mark events (`reference_id`)."""
    from project.presentation.shared.current_admin_unit import (
        get_current_admin_unit_for_api,
    )

    if not current_user or not current_user.is_authenticated:
        return None

    admin_unit = get_current_admin_unit_for_api()
    return admin_unit.id if admin_unit else None


def event_search_criteria_from_request(
    kwargs, defaults: Optional[dict] = None, **overrides
) -> EventSearchCriteria:
    """`defaults` yield to the request, `overrides` win over it."""
    args = request.args
    values = dict(defaults or {})
    values["trackable"] = trackable_criteria_from_kwargs(kwargs)
    sort = kwargs.get("sort")

    if sort:
        values["sort"] = EventSearchSort(sort)

    if "date_from" in args:
        values["date_from"] = form_input_to_date(args["date_from"])

    if "date_to" in args:
        values["date_to"] = form_input_to_date(args["date_to"], 23, 59, 59)

    if "keyword" in args:
        values["keyword"] = args["keyword"]

    coordinate = args.get("coordinate")

    if coordinate:
        values["latitude"], values["longitude"] = coordinate.split(",")

    if "distance" in args:
        values["distance"] = args["distance"]

    for arg, field in (
        ("category_id", "category_ids"),
        ("custom_category_set_id", "custom_category_set_ids"),
        ("postal_code", "postal_codes"),
        ("tag", "tags"),
        ("internal_tag", "internal_tags"),
    ):
        if arg in args:
            values[field] = list_arg_from_request(arg)

    if "weekday" in args:
        values["weekdays"] = args.getlist("weekday")

    for arg, field in (
        ("organizer_id", "organizer_id"),
        ("event_place_id", "event_place_id"),
        ("expected_participants_min", "expected_participants_min"),
        ("organization_id", "admin_unit_id"),
        ("admin_unit_id", "admin_unit_id"),
    ):
        if arg in args:
            values[field] = args[arg]

    if "status" in args:
        values["status"] = _members(EventStatus, list_arg_from_request("status"))

    if "public_status" in args:
        values["public_status"] = _members(
            EventPublicStatus, list_arg_from_request("public_status")
        )

    for arg, field in (
        ("exclude_recurring", "exclude_recurring"),
        ("include_organization_references", "include_admin_unit_references"),
        ("organization_references_only", "admin_unit_references_only"),
    ):
        if arg in args:
            values[field] = str_to_bool(args[arg])

    values.update(overrides)
    return EventSearchCriteria(**values)
