import functools
from dataclasses import dataclass
from typing import Optional, Type

from flask import Blueprint, jsonify, request
from pydantic import BaseModel
from werkzeug.wrappers import Response


@dataclass(frozen=True)
class RouteSpec:
    blueprint: Blueprint
    rule: str
    method: str
    endpoint: str
    query_model: Optional[Type[BaseModel]]
    body_model: Optional[Type[BaseModel]]
    response_model: Type[BaseModel]
    summary: Optional[str]

    @property
    def full_rule(self) -> str:
        """The URL rule including the prefixes of all parent blueprints."""
        prefix = _blueprint_prefix(self.blueprint)
        return prefix + self.rule


ROUTES: list[RouteSpec] = []

# Nested blueprints are registered by `init_bff`; the chain is resolved lazily so
# the spec can be built without an app.
_PARENTS: dict[Blueprint, Blueprint] = {}


def set_parent(child: Blueprint, parent: Blueprint) -> None:
    _PARENTS[child] = parent


def _blueprint_prefix(bp: Blueprint) -> str:
    prefix = bp.url_prefix or ""
    parent = _PARENTS.get(bp)
    if parent is not None:
        return _blueprint_prefix(parent) + prefix
    return prefix


def bff_route(
    bp: Blueprint,
    rule: str,
    *,
    method: str = "GET",
    query: Optional[Type[BaseModel]] = None,
    body: Optional[Type[BaseModel]] = None,
    response: Type[BaseModel],
    status: int = 200,
    summary: Optional[str] = None,
):
    """Register a JSON view on `bp` and record it for the OpenAPI document.

    The query string / JSON body are validated with the given pydantic models and
    passed to the view as the `query=` / `body=` keyword arguments. The return value
    is validated through `response` and serialized to JSON. A pydantic
    `ValidationError` propagates to the BFF error handler (422).
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            if query is not None:
                kwargs["query"] = query.model_validate(request.args.to_dict())
            if body is not None:
                kwargs["body"] = body.model_validate(request.get_json(silent=True))

            result = view(*args, **kwargs)
            if isinstance(result, Response):
                # e.g. the 401 of an auth decorator in front of the view
                return result
            payload = response.model_validate(result).model_dump(mode="json")
            return jsonify(payload), status

        bp.add_url_rule(rule, view_func=wrapper, methods=[method])
        ROUTES.append(
            RouteSpec(
                blueprint=bp,
                rule=rule,
                method=method.lower(),
                endpoint=f"{bp.name}.{view.__name__}",
                query_model=query,
                body_model=body,
                response_model=response,
                summary=summary,
            )
        )
        return wrapper

    return decorator
