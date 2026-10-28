"""Deprecated API routes: documented as `deprecated`, or hidden by a feature flag.

A route is declared deprecated once, at registration
(`add_api_resource(..., deprecated="<replacement>")`); `init_api` then either
registers it and marks it in the Swagger document, or leaves it out.
"""

from typing import Iterable, Optional

from flask_apispec.paths import rule_to_path

_OPERATIONS = {"get", "put", "post", "delete", "patch", "options", "head"}


def without_methods(resource_cls, methods: Iterable[str]):
    """A subclass of `resource_cls` that does not route `methods`, so the rule
    answers 405 for them (Flask's `MethodView` routes only `methods`)."""
    hidden = {method.upper() for method in methods}
    return type(
        f"Current{resource_cls.__name__}",
        (resource_cls,),
        {"methods": set(resource_cls.methods) - hidden},
    )


def mark_deprecated(
    app, spec, endpoint: str, replacement: str, methods: Optional[Iterable[str]] = None
) -> None:
    """Flag the registered operations of `endpoint` (all, or only `methods`) as
    `deprecated` in the Swagger document `spec`. Operations are marked on the
    document, never on the resource class, which the replacement routes share."""
    selected = {method.lower() for method in methods} if methods else None
    note = f"Deprecated, use {replacement}."

    for rule in app.url_map._rules_by_endpoint[endpoint]:
        for method, operation in spec._paths.get(rule_to_path(rule), {}).items():
            if method not in _OPERATIONS or (selected and method not in selected):
                continue
            operation["deprecated"] = True
            description = operation.get("description")
            operation["description"] = f"{note} {description}" if description else note
