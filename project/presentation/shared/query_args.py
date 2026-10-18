"""Map webargs kwargs of list endpoints onto query building blocks."""

from typing import Optional

from project.application.queries import PageRequest, TrackableCriteria, TrackableSort
from project.application.queries.page_request import DEFAULT_PER_PAGE


def page_request_from_kwargs(kwargs) -> PageRequest:
    """`PaginationRequestSchema` has already validated page and per_page."""
    return PageRequest(
        page=kwargs.get("page", 1),
        per_page=kwargs.get("per_page", DEFAULT_PER_PAGE),
    )


def trackable_criteria_from_kwargs(kwargs) -> TrackableCriteria:
    """Keys of `TrackableRequestSchemaMixin`; absent keys stay unbounded."""
    return TrackableCriteria(
        **{
            key: kwargs[key]
            for key in TrackableCriteria.model_fields
            if kwargs.get(key) is not None
        }
    )


def trackable_sort_from_kwargs(kwargs) -> Optional[TrackableSort]:
    """`TrackableRequestSchemaMixin.sort` has already validated the value."""
    sort = kwargs.get("sort")
    return TrackableSort(sort) if sort else None


def enum_or_none(enum_type, value):
    """Request values a schema accepts but a query enum does not know (e.g. the
    invitation `sort=name`) fall back to the default order, as the ORM path."""
    try:
        return enum_type(value)
    except ValueError:
        return None


def list_arg_from_request(name) -> list:
    """A repeated or comma-separated query arg, without "0" entries, as the legacy
    `BaseSearchParams.load_list_param`."""
    from flask import request

    values = request.args.getlist(name)

    if len(values) == 1 and "," in values[0]:
        values = [value.strip() for value in values[0].split(",")]

    return [value for value in values if value != "0"]
